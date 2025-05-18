from scipy.optimize import linear_sum_assignment
import numpy as np

cost_matrix = np.array([[4, 2, 5], [3, 3, 6], [7, 5, 1]])

row_ind, col_ind = linear_sum_assignment(cost_matrix)

print("cach gan cong nhan voi cong vie:")
for worker, job in zip(row_ind, col_ind):
    print(
        f"Cong nhan {worker} lam cong viec {job} voi chi phi {cost_matrix[worker, job]}"
    )

print("Tong chi phi:", cost_matrix[row_ind, col_ind].sum())
