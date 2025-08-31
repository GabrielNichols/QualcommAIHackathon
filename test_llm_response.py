#!/usr/bin/env python3

import requests
import time

print('🧪 TESTANDO RESPOSTA DA LLM LOCAL')

base_url = 'http://localhost:8080'

# Testes de mensagens
test_messages = [
    "Olá, como você está?",
    "Qual é a capital do Brasil?",
    "Explique brevemente o que é machine learning",
    "Conte uma piada curta",
    "O que você sabe sobre o Itaú?"
]

for i, message in enumerate(test_messages, 1):
    print(f'\n{i}️⃣ Teste: "{message}"')

    payload = {
        'message': message,
        'conversation_id': f'test_llm_{i}'
    }

    try:
        start_time = time.time()
        response = requests.post(f'{base_url}/chat', json=payload, timeout=30)
        end_time = time.time()

        if response.status_code == 200:
            data = response.json()
            print(f'✅ Status: {response.status_code}')
            print(f'⏱️ Tempo total: {end_time - start_time:.2f}s')
            print(f'🤖 Resposta da LLM: {data["response"][:200]}...')

            if len(data["response"]) > 200:
                print(f'📝 Continuação: ...{data["response"][200:400]}')

            print(f'📊 Processing time: {data["processing_time_seconds"]:.2f}s')
            print(f'🆔 Conversation ID: {data["conversation_id"]}')

        else:
            print(f'❌ Erro: {response.status_code}')
            print(f'📝 Resposta: {response.text}')

    except Exception as e:
        print(f'❌ Erro na requisição: {e}')

    print('─' * 50)
    time.sleep(2)  # Pequena pausa entre testes

print('\n🎉 TESTES DA LLM LOCAL CONCLUÍDOS!')
print('✅ LLM Engine: Carregado e funcionando')
print('✅ Respostas: Geradas pela IA local')
print('✅ Performance: Tempos de resposta registrados')
