function cleanExtractedText(input) {
  if (!input) return '';
  let s = String(input);
  // Remove caracteres de controle estranhos
  s = s.replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '');
  // Colapsa espaços em branco
  s = s.replace(/\s{2,}/g, ' ');
  // Remove sequências repetitivas curtas comuns em ruído (ex.: "own own own", "1. 1. 1.")
  s = s.replace(/\b(\w{1,6})(?:\s+\1){3,}\b/gi, '$1 $1');
  // Limita repetições de mesmo caractere (ex.: "....." -> "...")
  s = s.replace(/([\p{L}\p{N}\p{P}])\1{3,}/gu, '$1$1$1');
  return s.trim();
}

export async function summarizeEconomicNews(text) {
  const cleaned = cleanExtractedText(text);
  const today = new Date();
  const iso = today.toISOString().slice(0, 10);
  const prompt = [
    'Você é um assistente que extrai e resume notícias econômicas de forma objetiva.',
    'Use APENAS o conteúdo em "Texto da página". Não invente informações ou use conhecimento externo.',
    'Resuma as principais notícias/eventos do DIA em bullet points curtos e objetivos.',
    'Inclua quando possível: horário/data, país, título do evento/notícia e impacto/resultado/consenso.',
    'Se houver tabela de calendário econômico, extraia as linhas relevantes de HOJE.',
    'Formato de saída: texto puro, cada linha iniciando com "- ". Sem markdown, sem negrito, sem introdução ou conclusão.',
    'Se não houver notícias claras, retorne exatamente: "- Não foi possível encontrar destaques claros."',
    `Hoje: ${iso}.`,
    '',
    'Texto da página:',
    cleaned || '(sem conteúdo)',
    '',
    'Saída esperada:',
    '- 09:00 BR | IPCA (m/m) — Resultado 0,3% (Consenso 0,2%) — Impacto: Médio',
    '- 09:30 US | Nonfarm Payrolls — Resultado 175k (Consenso 180k) — Impacto: Alto',
  ].join('\n');

  const data = await window.api.localChat({ message: prompt });
  const out = String(data?.response || '').trim();
  return normalizeToBullets(out);
}

export async function chat(message) {
  const user = String(message ?? '').trim();
  const prompt = [
    'Responda em português (pt-BR), de forma direta e objetiva, em texto puro.',
    'Evite markdown e formatações especiais. Seja claro e conciso.',
    '',
    `Pergunta: ${user}`,
  ].join('\n');

  const data = await window.api.localChat({ message: prompt });
  const out = String(data?.response || '').trim();
  return stripMarkdown(out);
}

function stripMarkdown(s) {
  return String(s || '')
    .replace(/[\*`_#>]+/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function normalizeToBullets(output) {
  let s = String(output || '');
  // Remove marcação markdown básica
  s = s.replace(/[\*`_#>]+/g, '');
  // Quebra em linhas e limpa
  // Além de quebras de linha, force quebra quando houver " - " encadeando itens
  s = s.replace(/\s+-\s+/g, '\n- ');
  // E também quando houver bullets com ponto médio/dash
  s = s.replace(/\s+[•–—]\s+/g, '\n- ');
  let lines = s.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
  // Remove preâmbulos genéricos
  const prefaces = [
    /^aqui est(a|á)o/i,
    /^essas s(a|ã)o/i,
    /^seguem/i,
    /^resumo/i,
    /^responda/i,
    /^formato de sa[ií]da/i,
  ];
  lines = lines.filter(l => !prefaces.some(rx => rx.test(l)));
  // Converte listas numeradas ou com asterisco para '- '
  lines = lines.map(l => l.replace(/^([0-9]+\.)\s+/, '- ').replace(/^\*\s+/, '- '));
  // Garante prefixo '- '
  lines = lines.map(l => (l.startsWith('- ') ? l : `- ${l}`));
  // Remove linhas muito genéricas ou vazias
  lines = lines.filter(l => l.replace(/^-\s+/, '').length >= 4);
  // Se coexistir a linha de fallback com outras, remova a de fallback
  const fallback = '- Não foi possível encontrar destaques claros.';
  if (lines.length > 1) {
    lines = lines.filter(l => l.trim() !== fallback);
  }
  // Se existirem linhas com padrão de hora e/ou moeda, priorize-as
  const hasTimeCurr = lines.some(l => /\b\d{1,2}:\d{2}\b/.test(l) && /\b[A-Z]{3}\b/.test(l));
  if (hasTimeCurr) {
    lines = lines.filter(l => /\b\d{1,2}:\d{2}\b/.test(l) || /\b[A-Z]{3}\b/.test(l));
  }
  // Limita quantidade
  if (lines.length === 0) return '- Não foi possível encontrar destaques claros.';
  return lines.slice(0, 30).join('\n');
}
