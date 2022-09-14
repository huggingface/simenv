using UnityEngine;
using Newtonsoft.Json;
using System.Collections.Generic;

namespace SimEnv.GLTF {
    public class HFRaycastSensors {
        public List<HFRaycastSensor> objects;

        public HFRaycastSensors() {
            objects = new List<HFRaycastSensor>();
        }
        public class HFRaycastSensor {
            public int n_horizontal_rays;
            public int n_vertical_rays;
            public float horizontal_fov;
            public float vertical_fov;
            public float ray_length;
            public string sensor_name;
        }
    }
}