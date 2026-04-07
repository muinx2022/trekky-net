export default eventHandler(() => {
  throw createError({ statusCode: 501, statusMessage: "Google authentication is not available" });
});
