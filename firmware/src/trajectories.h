#include <Arduino.h>
#ifndef TRAJECTORY_H
# define TRAJECTORY_H


typedef struct Trajectory_1d {
  uint16_t *curve_a;
  uint32_t  len_a;
  uint32_t  distance_a;
  uint16_t *curve_d;
  uint32_t  len_d;
  uint32_t  distance_d;
} Trajectory_1d;

# define TRAJECTORIES_1D_COUNT 4
Trajectory_1d TRAJECTORIES_1D[TRAJECTORIES_1D_COUNT] = { 0 };

void clear_trajectory(Trajectory_1d *traj) {
  free(traj->curve_a);
  free(traj->curve_d);
  traj->curve_a = NULL;
  traj->curve_d = NULL;
}

void import_trajectory(uint8_t *data) {
  uint32_t index = ((uint32_t *)data)[0];

  data = data + 4;
  Trajectory_1d *src_struct = (Trajectory_1d *)data;
  Trajectory_1d *dst_struct = &TRAJECTORIES_1D[index];

  if (dst_struct->curve_a != NULL) {
    clear_trajectory(dst_struct);
  }
  dst_struct->len_a      = src_struct->len_a;
  dst_struct->len_d      = src_struct->len_d;
  dst_struct->distance_a = src_struct->distance_a;
  dst_struct->distance_d = src_struct->distance_d;

  uint32_t sizeof_a = src_struct->len_a * sizeof(uint16_t);
  uint32_t sizeof_d = src_struct->len_d * sizeof(uint16_t);
  dst_struct->curve_a = (uint16_t *)malloc(sizeof_a);
  dst_struct->curve_d = (uint16_t *)malloc(sizeof_d);

  memcpy(dst_struct->curve_a, data + sizeof(Trajectory_1d),            sizeof_a);
  memcpy(dst_struct->curve_d, data + sizeof(Trajectory_1d) + sizeof_a, sizeof_d);
}

#endif /* ifndef TRAJECTORY_H */
