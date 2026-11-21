"""Mixed layer depth (MLD) from CTD profiles, Plymouth Sound, 11 March 2026.

Data: 12 SeaBird CTD downcasts collected during MAR538 fieldwork (University of Plymouth).
Method:
  1. Remove records taken in air or at the surface before the sensor equilibrated
     (depth < 0.5 m; these show near-zero salinity).
  2. Compute potential density anomaly (sigma-theta) with TEOS-10 (gsw).
  3. Average into 0.5 m depth bins.
  4. MLD = depth where sigma-theta first exceeds its value at a 1 m reference depth by
     0.03 kg/m3 (de Boyer Montegut et al., 2004), with linear interpolation.
     The usual 10 m reference is replaced by 1.5 m because most stations are only 9-13 m deep;
     1.5 m sits below the thin, noisy surface skin. 1.0 m and 2.0 m are tested for sensitivity.
     If the threshold is never reached, the water column is mixed to the bottom.
  5. Sensitivity check with a 0.125 kg/m3 threshold (Monterey and Levitus, 1997).
"""
import glob, os
import numpy as np
import pandas as pd
import gsw
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LON, LAT = -4.14, 50.358          # central Plymouth Sound (survey area)
REF_DEPTH = 1.5                   # m (primary); 1.0 and 2.0 m tested for sensitivity
REF_TESTS = [1.0, 1.5, 2.0]
THRESHOLDS = [0.03, 0.125]        # kg/m3
BIN = 0.5                         # m

def read_cnv(path):
    text = open(path, errors="ignore").read()
    header, body = text.split("*END*")
    start = [l for l in header.splitlines() if "start_time" in l][0].split("=")[1].split("[")[0].strip()
    rows = [list(map(float, l.split()[:5])) for l in body.splitlines() if len(l.split()) >= 8]
    df = pd.DataFrame(rows, columns=["depth", "temp", "cond", "sal", "rho_insitu"])
    return df, start

def clean_and_bin(df):
    df = df[(df.depth >= 0.5) & (df.sal > 5)].copy()          # drop in-air / surface-soak records
    p = gsw.p_from_z(-df.depth.values, LAT)
    SA = gsw.SA_from_SP(df.sal.values, p, LON, LAT)
    CT = gsw.CT_from_t(SA, df.temp.values, p)
    df["sigma0"] = gsw.sigma0(SA, CT)
    df["zbin"] = np.floor(df.depth / BIN) * BIN + BIN / 2
    return df.groupby("zbin")[["temp", "sal", "sigma0"]].mean().reset_index()

def mld(prof, dsig, ref=REF_DEPTH):
    z, s = prof.zbin.values, prof.sigma0.values
    s_ref = np.interp(ref, z, s)
    zz = np.concatenate([[ref], z[z > ref]])
    ss = np.concatenate([[s_ref], s[z > ref]])
    hit = np.where(ss >= s_ref + dsig)[0]
    if len(hit) == 0:
        return float(z.max()), True                              # mixed to the bottom
    i = hit[0]
    return float(np.interp(s_ref + dsig, [ss[i - 1], ss[i]], [zz[i - 1], zz[i]])), False

results, profiles = [], {}
for path in sorted(glob.glob("data/ctd/*_conv.cnv")):
    station = "CTD" + os.path.basename(path).split("CTD")[1].split("_")[0].lstrip("0").zfill(2)
    raw, start = read_cnv(path)
    prof = clean_and_bin(raw)
    profiles[station] = prof
    row = dict(station=station, start_utc=start, max_depth_m=round(prof.zbin.max(), 2),
               surface_sal=round(prof.sal.iloc[0], 2), bottom_sal=round(prof.sal.iloc[-1], 2),
               delta_sigma0=round(prof.sigma0.iloc[-1] - prof.sigma0.iloc[0], 3))
    for t in THRESHOLDS:
        d, mixed = mld(prof, t)
        row[f"mld_{t}"] = round(d, 2)
        row[f"mixed_to_bottom_{t}"] = mixed
    for r in REF_TESTS:
        row[f"mld_0.03_ref{r}"] = round(mld(prof, 0.03, r)[0], 2)
    results.append(row)

res = pd.DataFrame(results)
res.to_csv("mld_results.csv", index=False)
print(res.to_string(index=False))

# Figure 1: sigma-theta profiles with MLD
fig, axes = plt.subplots(2, 6, figsize=(16, 7), sharex=True)
for ax, (st, prof) in zip(axes.flat, profiles.items()):
    r = res[res.station == st].iloc[0]
    ax.plot(prof.sigma0, prof.zbin, "-", color="tab:blue")
    ax.axhline(r["mld_0.03"], color="tab:red", lw=1.2, label="MLD (0.03)")
    ax.axhline(r["mld_0.125"], color="tab:orange", lw=1, ls="--", label="MLD (0.125)")
    ax.invert_yaxis()
    ax.set_title(f"{st}  MLD {r['mld_0.03']:.1f} m", fontsize=9)
    ax.tick_params(labelsize=8)
for ax in axes[:, 0]:
    ax.set_ylabel("Depth (m)")
for ax in axes[-1, :]:
    ax.set_xlabel(r"$\sigma_\theta$ (kg m$^{-3}$)")
axes.flat[0].legend(fontsize=7, loc="lower left")
fig.suptitle("Potential density profiles and mixed layer depth, Plymouth Sound, 11 March 2026")
fig.tight_layout()
fig.savefig("figures/mld_profiles.png", dpi=200)

# Figure 2: MLD vs water depth and stratification by station
fig, ax1 = plt.subplots(figsize=(10, 4.5))
x = np.arange(len(res))
ax1.bar(x, res.max_depth_m, color="lightgrey", label="Profile depth")
ax1.bar(x, res["mld_0.03"], color="tab:blue", label="MLD (0.03 kg/m³)")
ax1.invert_yaxis()
ax1.set_xticks(x); ax1.set_xticklabels(res.station, rotation=45)
ax1.set_ylabel("Depth (m)")
ax2 = ax1.twinx()
ax2.plot(x, res.delta_sigma0, "o-", color="tab:red", label=r"Top-to-bottom $\Delta\sigma_\theta$")
ax2.set_ylabel(r"$\Delta\sigma_\theta$ (kg m$^{-3}$)", color="tab:red")
h1, l1 = ax1.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, fontsize=8, loc="lower right")
ax1.set_title("Mixed layer depth and stratification by station, Plymouth Sound, 11 March 2026")
fig.tight_layout()
fig.savefig("figures/mld_by_station.png", dpi=200)
print("Saved mld_results.csv, figures/mld_profiles.png, figures/mld_by_station.png")
