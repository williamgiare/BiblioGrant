# -*- coding: utf-8 -*-
"""
BiblioGrant CLI entrypoint.

Run as:
    python -m BiblioGrant refs.bib [--order-by {keep_bib,publication_date,preprint_date}]
                                   [--reverse]
                                   [--compact]
                                   [--no-group-preprints]
                                   [--out output.txt]
"""

from __future__ import annotations
import argparse
from . import print_biblio, save_biblio

def main():
    p = argparse.ArgumentParser(
        description="Turn a BibTeX .bib file into a grant-friendly plain-text bibliography.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("bibfile", help="Path to the .bib file")
    p.add_argument(
        "--order-by",
        choices=["keep_bib", "publication_date", "preprint_date"],
        default="keep_bib",
        help="Sorting criterion",
    )
    p.add_argument(
        "--reverse",
        action="store_true",
        help="Reverse the chosen ordering (oldest first for date-based sorts; reverse .bib order for keep_bib)",
    )
    p.add_argument(
        "--compact",
        action="store_true",
        help="Compact mode: 'First Author et al., Venue Year, Vol(Issue): Pages' or 'First Author et al., arXiv:ID'",
    )
    p.add_argument(
        "--no-group-preprints",
        action="store_true",
        help="When using publication_date, do NOT print preprints and publications as separate sections",
    )
    p.add_argument(
        "--out",
        help="If provided, save to this file instead of printing to stdout",
    )

    args = p.parse_args()

    if args.out:
        save_biblio(
            bibfile=args.bibfile,
            out_path=args.out,
            order_by=args.order_by,
            reverse=args.reverse,
            group_preprints_on_publication=not args.no_group_preprints,
            compact=args.compact,
        )
    else:
        print_biblio(
            bibfile=args.bibfile,
            order_by=args.order_by,
            reverse=args.reverse,
            group_preprints_on_publication=not args.no_group_preprints,
            compact=args.compact,
        )

if __name__ == "__main__":
    main()
