import numpy as np
import pandas as pd 
import plotly.express as px
import plotly.graph_objects as go
from metrics import windowed_variance, variance
import optimal_plane
# 

folder = str(140412)
datachannel = str(0)

# Get the channel

datachannel = 'di'+datachannel+'P'
triggerchannel = 'di4P'

# Get the files

# dir_location = "/Users/perecornella/Library/CloudStorage/GoogleDrive-pere.cornella@estudiantat.upc.edu/My Drive/ReyesLabNYU/"

# rec = np.array([2,35])
# # rec = np.array([1,0,1])
# dir_location = dir_location + folder + "/"

# data, tonedata = read_in_data(dir_location, rec, datachannel, triggerchannel)

# locations = pd.read_csv('metadata/locations_' + folder + '.csv')
# new_locations = []
# for index, row in locations.iterrows():
#     interpolation_points = row['ff'] - row['f0']
#     interpolation_step = (row['xf'] - row['x0']) / interpolation_points
#     for i in range(row['f0'], row['ff'] + 1):
#         file = i_to_name(i, mode="d")
#         position = i - row['f0']
#         new_locations.append({
#             "Name": file,
#             "x": row['x0'] + position * interpolation_step, # Linear interpolation
#             "y": row['y'],
#             "z": row['z']
#         })

# locations = pd.DataFrame(new_locations)

# cfs = []
# for i in range(rec[0], rec[0] + rec[1]):
#     ad = activity(i, data, tonedata,
#                   metric = windowed_variance,
#                   title = "no_title",
#                   show = False, sort = False)

#     ad['Relevance'] = ad['Activity'] ** (-ad['Intensity']/10)
#     ad['Relevance'] = ad['Relevance'] / sum( ad['Relevance'] )
#     characteristic_frequency = sum(ad['Frequency'] * ad['Relevance'])
#     file = i_to_name(i, mode="d")
#     cfs.append({"Name": file, "CF": characteristic_frequency})

# cfs = pd.DataFrame(cfs)
# locations = pd.merge(cfs, locations, on='Name')


# ### PCA

# from sklearn.decomposition import PCA
# import matplotlib.pyplot as plt

# X = []
# for i, row in locations.iterrows():
#     X.append([row['x'], row['y'], row['z'], row['CF']])
# X = np.array(X)

# pca = PCA(n_components=3)
# fit = pca.fit_transform(X)

# fig = px.scatter(
#     locations,
#     x=fit[:, 0],
#     y=fit[:, 1],
#     color=fit[:, 2],
#     color_continuous_scale='Blues',
#     title=folder
# )

# fig.show()

value_of_interest = 'th'

# idea: find pairs

locations = pd.read_csv('metadata/di0P.csv')

# option 1: every point points to the closest one in CF
arrows = []
for i, base in locations.iterrows():
    tip = None
    min_dist = 1e99
    for j, aux in locations.iterrows():
        if aux['filename'] != base['filename']:
            dist = np.abs(aux[value_of_interest] - base[value_of_interest])
            if dist < min_dist:
                min_dist = dist
                tip = aux
    if tip is not None:
        arrows.append({
            "base_x": base['x'], "base_y": base['y'], "base_z": base['z'],
            "tip_x": tip['x'], "tip_y": tip['y'], "tip_z": tip['z']
        })

# option 2:
arrows = []

# Create a list to store all potential pairs with their CF differences
pairs = []
for i, base in locations.iterrows():
    for j, aux in locations.iterrows():
        if i != j:
            dist = np.abs(aux[value_of_interest] - base[value_of_interest])
            pairs.append({
                "base_index": i,
                "tip_index": j,
                "base_x": base['x'], "base_y": base['y'], "base_z": base['z'],
                "tip_x": aux['x'], "tip_y": aux['y'], "tip_z": aux['z'],
                "CF_diff": dist
            })

# Sort pairs by the smallest CF differences
pairs = sorted(pairs, key=lambda x: x['CF_diff'])

# Track used indices to ensure no repetition of points
used_indices = set()

# Select pairs without repetition (no point in more than one pair)
for pair in pairs:
    if pair['base_index'] not in used_indices and pair['tip_index'] not in used_indices:
        arrows.append({
            "base_x": pair['base_x'], "base_y": pair['base_y'], "base_z": pair['base_z'],
            "tip_x": pair['tip_x'], "tip_y": pair['tip_y'], "tip_z": pair['tip_z']
        })
        used_indices.add(pair['base_index'])
        used_indices.add(pair['tip_index'])
        

####### PLOT

fig = px.scatter_3d(
    locations,
    x='x',
    y='y',
    z='z',
    color=value_of_interest,
    hover_name='filename',
    color_continuous_scale='Blues',
    title=folder
)

# Update the scatter points to make them smaller
fig.update_traces(marker=dict(size=5))  # Adjust size as needed

# Add arrow lines
for arrow in arrows:
    fig.add_trace(go.Scatter3d(
        x=[arrow['base_x'], arrow['tip_x']],
        y=[arrow['base_y'], arrow['tip_y']],
        z=[arrow['base_z'], arrow['tip_z']],
        mode='lines',
        line=dict(width=2, color='blue'),
        showlegend=False  # Hide the line traces in the legend
    ))

# Add arrowheads as cones
for arrow in arrows:
    # Compute direction vectors
    u = arrow['tip_x'] - arrow['base_x']
    v = arrow['tip_y'] - arrow['base_y']
    w = arrow['tip_z'] - arrow['base_z']
    
    fig.add_trace(go.Cone(
        x=[arrow['tip_x']],  # Tip of the arrow
        y=[arrow['tip_y']],
        z=[arrow['tip_z']],
        u=[u],  # Direction vector components
        v=[v],
        w=[w],
        showscale=False,  # Hide scale for cones
        colorscale='Blues',  # Match line colors if desired
        sizemode="absolute",
        sizeref=50,
        anchor="tip"
    ))

# Save and display
fig.show()

result = optimal_plane.calculate(arrows)
optimal_A, optimal_B, optimal_C = result.x
print(f"Optimal unit vector: A={optimal_A}, B={optimal_B}, C={optimal_C}")


def project_point(x, y, z, A, B, C):
    d = A * x + B * y + C * z
    x_proj = x - d * A
    y_proj = y - d * B
    z_proj = z - d * C
    return x_proj, y_proj, z_proj

projected_points = []

for index, row in locations.iterrows():
    proj_x, proj_y, proj_z = project_point(row['x'], row['y'], row['z'], optimal_A, optimal_B, optimal_C)
    projected_points.append({
        'proj_x': proj_x,
        'proj_y': proj_y,
        'proj_z': proj_z,
        value_of_interest: row[value_of_interest],  
        'filename': row['filename']
    })

projected_df = pd.DataFrame(projected_points)

fig = px.scatter_3d(
    projected_df,
    x='proj_x',
    y='proj_y',
    z='proj_z',
    color=value_of_interest,
    hover_name='filename',
    color_continuous_scale='Blues',
    title='Projected Points onto Plane'
)

fig.update_traces(marker=dict(size=5))
fig.show()