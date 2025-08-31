export async function summarizeEconomicNews(text) {
  const prompt = [
    'Você é um assistente que extrai e resume notícias econômicas de forma objetiva.',
    'Resuma em bullet points as principais notícias, eventos e datas relevantes encontrados no texto da página.',
    'Inclua, quando possível: título/assunto, horário/data, países envolvidos e impacto esperado.',
    'Se não houver notícias claras, informe que não foi possível encontrar destaques.',
    '',
    'Texto da página:',
    text || '(sem conteúdo)',
    '',
    'Saída esperada:',
    '- Bullet points objetivos com títulos curtos',
  ].join('\n');

  const data = await window.api.localChat({ message: prompt });

  // O servidor local retorna { response, conversation_id, processing_time_seconds, timestamp }
  const out = data?.response || '';
  return String(out).trim();
}
