from typing import List, Dict, Tuple

class LevelAllocator:
    """
    A class to allocate levels to entries in the format "start-end".

    The level means that each number can only allocate one entry.
    The function will determine the level each entry is allocated based on previous allocations.

    Example:
        s = "1-2,3-4,1-4,2-3,3-5"
        allocator = LevelAllocator()
        levels = allocator.allocate_levels(s)  # Output: [1, 1, 2, 3, 4]
    """

    def __init__(self):
        self.allocation: Dict[int, int] = {}

    def get_level(self, ranges: List[Tuple[int, int]]) -> int:
        """
        Determines the next available level for the given range of numbers.

        Args:
            ranges (List[Tuple[int, int]]): List of tuples representing ranges.

        Returns:
            int: The next available level.
        """
        max_level = 0
        # Iterate over each range in the list of ranges
        for r in ranges:
            # Iterate over each number in the current range
            for i in range(r[0], r[1] + 1):
                # Check if the current number is already allocated
                if i in self.allocation:
                    # Update the maximum level found so far
                    max_level = max(max_level, self.allocation[i])
        # The next available level is one more than the maximum level found
        return max_level + 1

    def _allocate_level_for_entry(self, start: int, end: int) -> int:
        """
        Allocates a level for a single entry defined by its start and end.

        Args:
            start (int): The starting number of the range.
            end (int): The ending number of the range.

        Returns:
            int: The allocated level for this range.
        """
        level = self.get_level([(start, end)])
        # Update the allocation dictionary for each number in the current range
        for i in range(start, end + 1):
            self.allocation[i] = level
        return level

    def allocate_levels(self, s: str) -> List[int]:
        """
        Allocates levels to each entry in the input string.

        Args:
            s (str): A string containing entries in the format "start-end" separated by commas.

        Returns:
            List[int]: A list of integers representing the level of each entry.
        """
        entries = s.split(',')
        levels = []

        # Iterate over each entry in the list of entries
        for entry in entries:
            # Parse the start and end of the current range
            start, end = map(int, entry.split('-'))
            # Allocate the appropriate level for the current range
            level = self._allocate_level_for_entry(start, end)
            # Append the determined level to the levels list
            levels.append(level)

        return levels

    def get_entries_with_levels(self, s: str) -> List[Dict[str, int]]:
        """
        Returns a list of dictionaries with the levels associated to each entry.

        Args:
            s (str): A string containing entries in the format "start-end" separated by commas.

        Returns:
            List[Dict[str, int]]: A list of dictionaries, each containing 'start', 'end', and 'level'.
        """
        entries = s.split(',')
        result = []

        # Iterate over each entry in the list of entries
        for entry in entries:
            # Parse the start and end of the current range
            start, end = map(int, entry.split('-'))
            # Allocate the appropriate level for the current range
            level = self._allocate_level_for_entry(start, end)
            # Append a dictionary with start, end, and level to the result list
            result.append({
                'start': start,
                'end': end,
                'level': level,
            })

        return result
