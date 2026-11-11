import json
import requests
import time
import os

API_URL = "http://127.0.0.1:8000"

def load_questions():
    with open("data/eval_questions.json", "r", encoding="utf-8") as f:
        return json.load(f)

def run_evaluation():
    questions = load_questions()
    print(f"Загружено {len(questions)} вопросов. Начинаю тестирование...\n")
    
    # Сначала убедимся, что документ загружен
    print("Загружаю документ в API...")
    resp = requests.post(f"{API_URL}/load_document")
    if resp.status_code != 200:
        print("Ошибка загрузки документа. Запущен ли сервер?", resp.text)
        return

    results = []
    
    for q in questions:
        q_id = q["id"]
        question = q["question"]
        ref_answer = q["reference_answer"]
        
        print(f"[{q_id}/{len(questions)}] Вопрос: {question}")
        
        try:
            # Отправляем вопрос в наш FastAPI
            response = requests.post(
                f"{API_URL}/ask",
                json={"question": question},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                model_answer = data["answer"]
                
                # Оцениваем попадание (Hit Rate)
                # Если в правильном ответе написано "НЕТ_ОТВЕТА", 
                # проверяем, что модель тоже написала "нет ответа"
                is_correct = False
                if ref_answer == "НЕТ_ОТВЕТА":
                    if "нет ответа" in model_answer.lower() or "не содержит" in model_answer.lower():
                        is_correct = True
                else:
                    # Если есть правильный ответ, проверяем совпадение ключевых слов
                    # (простая проверка, так как нейросеть может перефразировать)
                    ref_words = set(ref_answer.lower().split())
                    model_words = set(model_answer.lower().split())
                    # Если совпало хотя бы 50% слов из эталона
                    intersection = ref_words.intersection(model_words)
                    if len(intersection) >= len(ref_words) * 0.5:
                        is_correct = True
                
                results.append({
                    "id": q_id,
                    "is_correct": is_correct,
                    "ref": ref_answer,
                    "model": model_answer
                })
                print(f"  -> {'ВЕРНО' if is_correct else 'ОШИБКА'}")
            else:
                print(f"  -> Ошибка API: {response.status_code}")
                results.append({"id": q_id, "is_correct": False, "error": response.text})
                
        except Exception as e:
            print(f"  -> Ошибка соединения: {e}")
            results.append({"id": q_id, "is_correct": False, "error": str(e)})
            
        time.sleep(1) # Пауза, чтобы не превысить лимиты Yandex API

    # Считаем итоги
    correct_count = sum(1 for r in results if r.get("is_correct"))
    total = len(results)
    hit_rate = (correct_count / total) * 100 if total > 0 else 0
    
    print("\n" + "="*40)
    print(f"ИТОГОВЫЙ РЕЗУЛЬТАТ:")
    print(f"Правильных ответов: {correct_count} из {total}")
    print(f"Hit Rate (Точность): {hit_rate:.1f}%")
    print("="*40)
    
    # Сохраняем отчет
    with open("data/eval_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "hit_rate": hit_rate,
            "total": total,
            "correct": correct_count,
            "details": results
        }, f, ensure_ascii=False, indent=2)
    print("Детальный отчет сохранен в data/eval_results.json")

if __name__ == "__main__":
    run_evaluation()
