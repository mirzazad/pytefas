"""pytefas temel kullanım örnekleri."""
from pytefas import Crawler


def main():
    tefas = Crawler()

    # 1. Tek gün, fiyat bilgisi (YAT fonları)
    print("=== Fiyat bilgisi (YAT, 2026-04-24) ===")
    df = tefas.fetch("2026-04-24", columns="info", kind="YAT")
    print(f"Toplam fon: {len(df)}")
    print(df[["fund_code", "fund_name", "price", "portfolio_size"]].head())
    print()

    # 2. Aynı gün, portföy dağılımı
    print("=== Portföy dağılımı (YAT, 2026-04-24) ===")
    df = tefas.fetch("2026-04-24", columns="breakdown", kind="YAT")
    aak = df[df["fund_code"] == "AAK"].iloc[0]
    nonzero = {k: v for k, v in aak.items() if isinstance(v, (int, float)) and v}
    print(f"AAK varlık dağılımı: {nonzero}")
    print()

    # 3. Tüm fon tiplerini birlikte
    print("=== Tüm tipler (2026-04-24) ===")
    df = tefas.fetch_many("2026-04-24", columns="info")
    print(df.groupby("kind").size())
    print()

    # 4. Tarih aralığı
    print("=== Tarih aralığı (2026-04-22 → 2026-04-24, YAT) ===")
    df = tefas.fetch(start="2026-04-22", end="2026-04-24", columns="info", kind="YAT")
    print(df.groupby("date").size())


if __name__ == "__main__":
    main()
