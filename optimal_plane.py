# Author CHATGPT
# Modifications Pere Cornella

from scipy.optimize import minimize
import numpy as np

# Function to calculate the projected distance of a segment onto a plane Ax + By + Cz = 0
def projected_distance(arrow, A, B, C):
    # Coordinates of the two points defining the segment
    x1, y1, z1 = arrow['base_x'], arrow['base_y'], arrow['base_z']
    x2, y2, z2 = arrow['tip_x'], arrow['tip_y'], arrow['tip_z']
    
    # Direction vector of the segment
    dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
    
    # Dot product of the segment direction and the normal vector (A, B, C)
    dot_product = dx * A + dy * B + dz * C
    
    # Projected distance squared
    total_distance_squared = dx**2 + dy**2 + dz**2
    projected_distance_squared = total_distance_squared - (dot_product**2)
    return np.sqrt(max(projected_distance_squared, 0))

# Main function
def calculate(arrows):

        # Objective function to minimize
    def objective(params):
        A, B, C = params  # Plane normal vector components
        total_distance = 0
        for arrow in arrows:
            total_distance += projected_distance(arrow, A, B, C)
        return total_distance

    # Constraint: A^2 + B^2 + C^2 = 1 (unit vector constraint)
    def constraint(params):
        A, B, C = params
        return A**2 + B**2 + C**2 - 1

    # Initial guess for (A, B, C)
    initial_guess = np.array([1.0, 0.0, 0.0])

    # Optimization
    result = minimize(
        objective,
        initial_guess,
        constraints={'type': 'eq', 'fun': constraint},  # Unit vector constraint
        method='SLSQP'
    )

    return result