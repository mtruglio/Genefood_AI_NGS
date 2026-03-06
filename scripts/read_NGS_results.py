from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple, Union, Optional
import re

import pandas as pd


def _pick_engine(excel_path: Union[str, Path]) -> Optional[str]:
    """
    Pick a pandas read_excel engine based on file extension.
    - .xlsx/.xlsm -> openpyxl
    - .xls -> xlrd (requires `pip install xlrd`)
    """
    print("Determining engine for file:", excel_path)
    p = Path(excel_path.filename)
    ext = p.suffix.lower()

    if ext in {".xlsx", ".xlsm", ".xltx", ".xltm"}:
        return "openpyxl"
    if ext == ".xls":
        # pandas needs xlrd for legacy .xls
        return "xlrd"
    return None  # let pandas try (may still fail)


def _find_col(df: pd.DataFrame, target: str) -> str:
    """
    Find a column in df matching `target` ignoring case and extra spaces.
    Raises KeyError if not found.
    """
    tgt = re.sub(r"\s+", " ", target).strip().casefold()
    for c in df.columns:
        c_norm = re.sub(r"\s+", " ", str(c)).strip().casefold()
        if c_norm == tgt:
            return c
    raise KeyError(f"Required column not found: {target!r}. Available: {list(df.columns)!r}")


def _split_allele_name(allele_name: object) -> Tuple[str, str]:
    """
    Split 'Allele Name' into (Gene, rsID):
    - split by underscore
    - rightmost element must start with 'rs' (case-insensitive), otherwise error
    - left side joined back with underscores (gene may contain underscores)
    """
    if allele_name is None or (isinstance(allele_name, float) and pd.isna(allele_name)):
        raise ValueError("Allele Name is missing (NaN/None).")

    s = str(allele_name).strip()
    parts = s.split("_")
    if len(parts) < 2:
        raise ValueError(f"Allele Name {s!r} does not contain an underscore; cannot split into Gene and rsID.")

    rsid = parts[-1].strip()
    if not rsid.casefold().startswith("rs"):
        raise ValueError(
            f"Allele Name {s!r} does not end with an rsID-like token. "
            f"Expected last underscore-separated token to start with 'rs', got {rsid!r}."
        )

    gene = "_".join(parts[:-1]).strip()
    if not gene:
        raise ValueError(f"Allele Name {s!r} has empty Gene part after splitting.")
    return gene, rsid


def build_pandas_variant_db(
    excel_path: Union[str, Path],
    sheet_name: Union[int, str] = 0,
    as_dict: bool = False,
) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """
    Read an Excel file and build a pandas "database" keyed by 'Sample Name'.

    Keeps columns:
      - Sample Name
      - Ref
      - Variant
      - Allele Call
      - Allele Source   (rows with value 'Novel' are removed)
      - Allele Name     (split into Gene and rsID)

    Output:
      - if as_dict=False (default): a DataFrame indexed by 'Sample Name' (duplicates allowed; use df.loc[sample])
      - if as_dict=True: dict {sample_name: DataFrame_of_rows_for_that_sample}

    Notes:
      - For legacy .xls you need: pip install xlrd
      - Column matching is case/space-insensitive.
    """
    # Determine filename to check extension
    # Handles both string paths and FileStorage objects (which have .filename)
    filename = getattr(excel_path, "filename", str(excel_path))
    ext = Path(filename).suffix.lower()

    if ext == ".xls":
        # Treat .xls as tab-separated values (TSV)
        try:
            df = pd.read_csv(excel_path, sep="\t")
        except Exception as e:
            raise ValueError(f"Failed to read .xls file as TSV: {e}") from e
    else:
        engine = _pick_engine(excel_path)

        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name, engine=engine)
        except ImportError as e:
            # Typical when .xls but xlrd missing
            raise ImportError(
                "Reading this Excel file requires an extra dependency.\n"
                "If your file is .xls (legacy Excel), install xlrd:\n"
                "  pip install xlrd\n"
                "Or convert the file to .xlsx and re-run."
            ) from e

    # Resolve required columns robustly
    c_sample = _find_col(df, "Sample Name")
    c_ref = _find_col(df, "Ref")
    c_variant = _find_col(df, "Variant")
    c_call = _find_col(df, "Allele Call")
    c_source = _find_col(df, "Allele Source")
    c_allele_name = _find_col(df, "Allele Name")

    # Filter out Novel rows in Allele Source
    source_series = df[c_source].astype(str).str.strip()
    df = df.loc[source_series.ne("Novel")].copy()

    # Split Allele Name -> Gene, rsID (strict check on rsID)
    gene_rsid = df[c_allele_name].map(_split_allele_name)
    df["Gene"] = gene_rsid.map(lambda x: x[0])
    df["rsID"] = gene_rsid.map(lambda x: x[1])

    # Keep requested columns (+ derived Gene/rsID)
    out = df[[c_sample, c_ref, c_variant, c_call, c_source, "Gene", "rsID"]].copy()
    out = out.rename(columns={c_sample: "Sample Name", c_ref: "Ref", c_variant: "Variant",
                              c_call: "Allele Call", c_source: "Allele Source"})
    out["Sample Name"] = out["Sample Name"].astype(str).str.strip()

    # Key by Sample Name
    out = out.set_index("Sample Name").sort_index()

    if not as_dict:
        return out

    # Dict keyed by sample
    return {s: out.loc[[s]].copy() for s in out.index.unique()}


# -------------------- quick usage --------------------
# df_db = build_pandas_variant_db("your_file.xls")          # DataFrame indexed by Sample Name
# one_patient = df_db.loc["PATIENT_001"]                    # returns a DataFrame (or Series if single row)
# db_dict = build_pandas_variant_db("your_file.xls", as_dict=True)
# one_patient_df = db_dict["PATIENT_001"]
