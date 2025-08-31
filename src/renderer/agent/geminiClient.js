export async function summarizeEconomicNews(text) {
  const prompt = [
    'Você é um assistente que extrai e resume notícias econômicas de forma objetiva.',
    'Resuma em bullet points as principais notícias, eventos e datas relevantes encontrados no texto da página.',
    'Inclua, quando possível: título/assunto, horário/data, países envolvidos e impacto esperado.',
    'Se não houver notícias claras, informe que não foi possível encontrar destaques.',
    '',
    'Texto da página:',
    text || '(sem conteúdo)',
  ].join('\n');

  const body = {
    contents: [
      {
        role: 'user',
        parts: [{ text: prompt }],
      },
    ],
    generationConfig: {
      temperature: 0.3,
      maxOutputTokens: 600,
    },
  };

  const data = await window.api.geminiGenerate(body);
  const out =
    data?.candidates?.[0]?.content?.parts?.map((p) => p.text).join('') || '';
  return out.trim();
}
