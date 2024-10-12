from csvw.dsv import UnicodeDictReader
import cartopy.feature as cfeature
import cartopy.crs as ccrs
from matplotlib import pyplot as plt


data = []
with UnicodeDictReader("map-data-annotated.tsv", delimiter="\t") as reader:
    for row in reader:
        data += [row]

print("loaded data")
plt.clf()


fig = plt.figure(figsize=[20, 10])

data_crs = ccrs.PlateCarree()
ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
ax.coastlines(resolution='50m')
ax.add_feature(cfeature.LAND)
ax.add_feature(cfeature.OCEAN)
ax.add_feature(cfeature.BORDERS, linestyle=':')
ax.add_feature(cfeature.LAKES, alpha=0.5)
ax.add_feature(cfeature.RIVERS)


sizes = set([int(row["Sources"]) for row in data])
size_list = [int(row["Sources"]) for row in data]
colors = {
                    "Africa": "#e41a1c",
                    "Australia": "#377eb8",
                    "North America": "#4daf4a", #darkorange",
                    "South America": "#984ea3", #saddlebrown",
                    "Papunesia": "#ff7f00",
                    "Eurasia": "#ffff33"
                    }


count = 0
for row in sorted(data, key=lambda x: int(x["Sources"]), reverse=True):
    if row["Longitude"] != "None" and row["Latitude"] != "None":
        plt.plot(
                float(row["Longitude"]),
                float(row["Latitude"]),
                "o",
                color=colors[row["Macroarea"]],
                markersize=5,
                markeredgewidth=0.1,
                markeredgecolor="black"
                )
    else:
        count += 1


legend, legend_labels = [], []
for point, name in [
        ["North America", "North America"],
        ["South America", "South America"],
        ["Eurasia", "Eurasia"],
        ["Africa", "Africa"],
        ["Papunesia", "Papunesia"],
        ["Australia", "Australia"]]:
    point = plt.plot(0, 5000, "o", color=colors[point], markersize=1.5 * 6,
                     label=name,
                     markeredgewidth=0.1, markeredgecolor="black"

                     )
    legend += point
    legend_labels += [name]




legend = plt.legend(legend, legend_labels, loc=3, prop={'size': 16})

plt.gca().add_artist(legend)
plt.savefig("map.pdf")
plt.savefig("map.jpg")
