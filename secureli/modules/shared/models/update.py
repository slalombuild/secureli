from typing import Optional

import pydantic


class UpdateResult(pydantic.BaseModel):
    """
    The results of calling scan_repo
    """

    successful: bool
    output: Optional[str] = None
