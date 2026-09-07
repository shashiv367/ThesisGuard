from datasketch import MinHash, MinHashLSH

def get_minhash(text: str, n: int = 5, num_perm: int = 128) -> MinHash:
    """Builds a MinHash from n-gram word shingles."""
    m = MinHash(num_perm=num_perm)
    words = text.split()
    
    # Handle short texts
    if len(words) < n:
        m.update(text.encode("utf8"))
        return m
        
    for i in range(len(words) - n + 1):
        shingle = " ".join(words[i:i + n])
        m.update(shingle.encode("utf8"))
    return m

def build_exact_match_index(source_chunks: list[str], threshold: float = 0.5):
    """Builds and returns a MinHashLSH index plus a dict mapping chunk index to its MinHash."""
    lsh = MinHashLSH(threshold=threshold, num_perm=128)
    minhashes = {}
    for idx, chunk in enumerate(source_chunks):
        mh = get_minhash(chunk)
        minhashes[idx] = mh
        lsh.insert(str(idx), mh)
    return lsh, minhashes

def check_exact_match(query_chunk: str, lsh: MinHashLSH, minhashes: dict) -> list[int]:
    """Returns indices of matching source chunks above the similarity threshold."""
    q_mh = get_minhash(query_chunk)
    result_keys = lsh.query(q_mh)
    # result_keys are strings like "0", "1"
    return [int(k) for k in result_keys]
