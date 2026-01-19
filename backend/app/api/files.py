"""
File content endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class FileContent(BaseModel):
    path: str
    content: str
    language: Optional[str]
    size_bytes: int
    line_count: int


# Demo code
_demo_code = '''import itertools
import random

class Minesweeper():
    """
    Minesweeper game representation
    """

    def __init__(self, height=8, width=8, mines=8):
        
        # Set initial width, height, and number of mines
        self.height = height
        self.width = width
        self.mines = set()
        
        # Initialize an empty field with no mines
        self.board = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(False)
            self.board.append(row)
        
        # Add mines randomly
        while len(self.mines) != mines:
            i = random.randrange(self.height)
            j = random.randrange(self.width)
            if not self.board[i][j]:
                self.mines.add((i, j))
                self.board[i][j] = True
        
        # At first, player has found no mines
        self.mines_found = set()

    def print(self):
        """
        Prints a text-based representation
        of where mines are located.
        """
        for i in range(self.height):
            print("--" * self.width + "-")
            for j in range(self.width):
                if self.board[i][j]:
                    print("|X", end="")
                else:
                    print("| ", end="")
            print("|")
        print("--" * self.width + "-")

    def is_mine(self, cell):
        i, j = cell
        return self.board[i][j]

    def nearby_mines(self, cell):
        """
        Returns the number of mines that are
        within one row and column of a given cell,
        not including the cell itself.
        """
        count = 0
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):
                if (i, j) == cell:
                    continue
                if 0 <= i < self.height and 0 <= j < self.width:
                    if self.board[i][j]:
                        count += 1
        return count

    def won(self):
        """
        Checks if all mines have been flagged.
        """
        return self.mines_found == self.mines
'''


@router.get("", response_model=FileContent)
async def get_file_content(snapshot_id: str, path: str = Query(...)):
    """Get file content by path"""
    # Demo response
    if "minesweeper.py" in path:
        return FileContent(
            path=path,
            content=_demo_code,
            language="python",
            size_bytes=len(_demo_code),
            line_count=_demo_code.count("\n") + 1,
        )
    
    if path.endswith(".md"):
        return FileContent(
            path=path,
            content="# Welcome to the Demo Project\n\nDouble-click to explore!",
            language="markdown",
            size_bytes=50,
            line_count=3,
        )
    
    raise HTTPException(status_code=404, detail="File not found")
