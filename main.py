import sys
import pickle

from pprint import pprint

from tqdm import tqdm

from cache.msi import MSICache
from cache.mesi import MESICache
from cache.mes import MESCache
from utils import int_or_None


stats = {"MSICache": {},
         "MESICache": {},
         "MESCache": {}}
def record_stats(caches):
    global stats
    for cache in caches:
        stats[cache.__class__.__name__][cache.block_size] = cache.stats

def print_stats(caches, line):
    for cache in caches:
        if line == "h":
            print("Hit Rate P%d R:%d W:%d" % (cache.cpu_id,
                                              cache.stats["R"]["HIT"],
                                              cache.stats["W"]["HIT"]))
        elif line == "i":
            print("Invalidations P%d %d" % (cache.cpu_id,
                                            cache.stats["INVALIDATED"]))
        elif line == "p":
            print("Cache P%d %s" % (cache.cpu_id,
                                    [int_or_None(v) for v in cache.store]))
        elif line == "s":
            sys.stdout.write("P%d: " % cache.cpu_id)
            pprint(cache.stats)

def parse_line(line):
    if len(line) == 1:
        return (None, line, None)

    cpu_id, op, address = line.split(" ")
    cpu_id = int(cpu_id.lstrip("P"))
    address = int(address, 16)
    binaddr = bin(address)[2:].zfill(32)
    return (cpu_id, op, binaddr)

def run_stages(caches, cpu_id, op, address):
    for cache in caches:
        cache.stage1()

    if op in ("R", "W"):
        for cache in caches:
            cache.stage2(cpu_id, op, address)


if __name__ == "__main__":
    with open("trace", "r") as f:
        lines = f.readlines()

    buses = ([], [], [], [])
    block_sizes = (2, 4, 8, 16)
    for cache in (MSICache, MESICache, MESCache):
        for block_size in block_sizes:
            caches = []
            for cpu_id in range(4):
                caches.append(cache(cpu_id, buses, block_size=block_size))

            print("Processing trace with %s at block size %d..." % (caches[-1].__class__.__name__, block_size))
            for line in tqdm(lines, leave=True):
                cpu_id, op, address = parse_line(line)
                if op in ("h", "i", "p", "s"):
                    print_stats(caches, op)
                else:
                    run_stages(caches, cpu_id, op, address)

#            print_stats(caches, "s")
            record_stats(caches)

    with open("stats-block_size.pkl", "wb") as f:
        pickle.dump(stats, f)
