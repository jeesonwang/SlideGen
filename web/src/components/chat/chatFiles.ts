interface FileLike {
  id: string;
}

interface FilesPayloadLike {
  data?: FileLike[] | null;
}

export const getCurrentFileIds = (filesData?: FilesPayloadLike | null): string[] => {
  if (!Array.isArray(filesData?.data)) {
    return [];
  }

  return filesData.data.map((file) => file.id);
};
