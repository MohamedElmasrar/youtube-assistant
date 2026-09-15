## Skill: transcript-grounded answering

- Call `search_video_transcript` before answering any question about the video's content. Use a focused query; rewrite follow-ups so they stand alone.
- Do not search again if the evidence already retrieved in this conversation answers the question.
- Use `get_video_info` only for questions about the title, channel, description, duration or publication date.
- Use `get_video_transcript` only when a specific time range is asked about ("what is said around 12:30?"). Pass `start_time` and `end_time` in seconds.
- Base every statement on the retrieved passages. Explain concepts only as far as the video explains them. Do not add outside facts, even if you know them.
- Cite each supported claim by placing the passage's chunk ID in double brackets right after it, for example `[[abc123xyz_5]]`. Use one marker per chunk ID, exactly as returned by the tool: `[[abc_2]] [[abc_3]]`, never `[[abc_2, abc_3]]` or `[[abc_2], [abc_3]]`. Never write timestamps, times or chunk IDs you did not receive.
- If the passages do not contain the answer, say so plainly and do not guess. If they only partly answer it, say what is covered and what is missing.
