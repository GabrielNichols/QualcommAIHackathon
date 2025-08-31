export async function handleOpenSiteRequest({
  url,
  openInNewTab,
  waitForLoad,
  capturePage,
  summarize,
}) {
  await openInNewTab(url);
  await waitForLoad(url); // aguarda o load da nova navegação
  // Aguarda mais um pouco para SPAs/renderizações tardias (ex.: investing.com)
  await new Promise((r) => setTimeout(r, 1500));
  const capture = await capturePage({ save: false }).catch((e) => ({ text: '', error: String(e || '') }));
  const text = capture?.text || '';
  const summary = await summarize(text);
  return { url, capture, summary };
}
