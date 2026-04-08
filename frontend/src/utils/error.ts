export function friendlyPublishError(message: string): string {
  if (
    message.includes("Session has expired") ||
    message.includes("Error validating access token") ||
    message.includes('"code":190') ||
    message.includes("OAuthException")
  ) {
    return "Instagram authentication expired. Please reconnect or refresh the Facebook/Instagram access token, then try publishing again.";
  }

  if (
    message.includes("Media download has failed") ||
    message.includes("media URI doesn't meet our requirements") ||
    message.includes("Only photo or video can be accepted as media type")
  ) {
    return "Instagram could not fetch the media file. Check that the backend has a public URL and that the media file type is supported.";
  }

  if (message.includes("Invalid timezone")) {
    return "The selected timezone is invalid.";
  }

  if (message.includes("ApprovedPost not found")) {
    return "This approved post could not be found.";
  }

  if (message.includes("Failed to publish now")) {
    return "The post could not be queued for immediate publishing.";
  }

  if (message.includes("Failed to schedule")) {
    return "The post could not be scheduled.";
  }

  return message;
}
