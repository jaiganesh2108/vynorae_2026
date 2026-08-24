import osmnx as ox
import os

# Create output folder
output_folder = "chennai_osm_data"
os.makedirs(output_folder, exist_ok=True)

# Download Chennai road network
G = ox.graph_from_place(
    "Chennai, Tamil Nadu, India",
    network_type="drive"
)

# Convert graph to GeoDataFrames
nodes, edges = ox.graph_to_gdfs(G)

# Save files inside the folder
nodes.to_csv(
    os.path.join(output_folder, "chennai_nodes.csv"),
    index=True
)

edges.to_csv(
    os.path.join(output_folder, "chennai_roads.csv"),
    index=True
)

print("Download completed!")
print("Nodes:", len(nodes))
print("Roads:", len(edges))
print(f"Files saved inside: {output_folder}/")