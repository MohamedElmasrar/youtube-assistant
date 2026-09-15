## Skill: video summarization

The user wants a summary or overview. Cover the whole video, not just its beginning.

1. Call `get_video_info` for the duration if it is not yet known.
2. Read the transcript with `get_video_transcript`. If `truncated` is true, call it again with `start_time` set to `next_start_time`, until the end or until the tool budget is nearly used.
3. Call `search_video_transcript` once or twice on the main topics, so the key points can be cited with chunk IDs.
4. Write a structured summary: one-sentence overview, then the key topics in the order the video presents them (short headings or bullets), then main takeaways.
5. Use only what the transcript says. No external claims. Cite key points with `[[chunk_id]]` markers from search results only. If part of the video could not be read, say so.
