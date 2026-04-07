function genId(): string {
  return Date.now().toString(16) + Math.random().toString(16).slice(2, 8);
}

function getExt(file: File): string {
  const fromName = file.name.split(".").pop()?.toLowerCase();
  if (fromName && fromName.length <= 5) return fromName;
  const fromMime: Record<string, string> = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
    "image/avif": "avif",
    "video/mp4": "mp4",
    "video/webm": "webm",
  };
  return fromMime[file.type] ?? "bin";
}

export function nameAvatarFile(file: File): File {
  const name = `trekky-net-avatar-${genId()}.${getExt(file)}`;
  return new File([file], name, { type: file.type });
}

export function nameGalleryFile(file: File): File {
  const prefix = file.type.startsWith("video/") ? "trekky-net-gallery-video" : "trekky-net-gallery-image";
  return new File([file], `${prefix}-${genId()}.${getExt(file)}`, { type: file.type });
}

export function nameContentFile(file: File): File {
  const prefix = file.type.startsWith("video/") ? "trekky-net-content-video" : "trekky-net-content-image";
  return new File([file], `${prefix}-${genId()}.${getExt(file)}`, { type: file.type });
}
