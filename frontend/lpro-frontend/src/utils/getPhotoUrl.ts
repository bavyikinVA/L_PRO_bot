export const getPhotoUrl = (photoPath?: string | null) => {
  if (!photoPath) {
    return "";
  }

  if (photoPath.startsWith("app/static/")) {
    return "/" + photoPath.replace("app/static/", "static/");
  }

  if (photoPath.startsWith("/app/static/")) {
    return photoPath.replace("/app/static/", "/static/");
  }

  if (photoPath.startsWith("static/")) {
    return "/" + photoPath;
  }

  if (photoPath.startsWith("/static/")) {
    return photoPath;
  }

  if (photoPath.startsWith("http://") || photoPath.startsWith("https://")) {
    return photoPath;
  }

  return photoPath;
};