export function stripSubredditPrefix(sub: string): string {
  return sub.replace(/^\/?(r\/)+/, "");
}
