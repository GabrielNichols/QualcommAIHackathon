export async function handleOpenSiteRequest({
  url,
  openInNewTab,
  waitForLoad,
  capturePage,
  summarize,
}) {
  await openInNewTab(url);
  await waitForLoad(url); // aguarda o load da nova navegação
  const capture = await capturePage({ save: false });
  const text = capture?.text || '';
  const summary = await summarize(text);
  return { url, capture, summary };
}
