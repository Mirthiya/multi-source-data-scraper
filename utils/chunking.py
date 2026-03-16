def chunk_text(paragraphs, chunk_size=3):

    chunks = []

    for i in range(0, len(paragraphs), chunk_size):
        chunk = " ".join(paragraphs[i:i+chunk_size])
        chunks.append(chunk)

    return chunks
