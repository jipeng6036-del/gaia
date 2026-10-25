async page => {
  await page.route('**/api/setup/check?*', async route => {
    const url = new URL(route.request().url());
    url.searchParams.set('skip_chat_model', 'true');
    await route.continue({url: url.toString()});
  });
  await page.reload();
}
