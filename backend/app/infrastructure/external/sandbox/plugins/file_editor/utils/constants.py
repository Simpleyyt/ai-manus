MAX_RESPONSE_LEN_CHAR: int = 16000

CONTENT_TRUNCATED_NOTICE = "<response clipped><NOTE>Due to the max output limit, only part of the full response has been shown to you.</NOTE>"  # noqa: E501

TEXT_FILE_CONTENT_TRUNCATED_NOTICE: str = "<response clipped><NOTE>Due to the max output limit, only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>"  # noqa: E501

BINARY_FILE_CONTENT_TRUNCATED_NOTICE: str = "<response clipped><NOTE>Due to the max output limit, only part of this file has been shown to you. Please use Python libraries to view the entire file or search for specific content within the file.</NOTE>"  # noqa: E501

DIRECTORY_CONTENT_TRUNCATED_NOTICE: str = "<response clipped><NOTE>Due to the max output limit, only part of this directory has been shown to you. You should use `ls -la` instead to view large directories incrementally.</NOTE>"  # noqa: E501
