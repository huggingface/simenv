using System.Collections;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.Rendering.Universal;

namespace SimEnv {
    public class RenderCamera {
        public Node node => m_node;
        public Camera camera => m_camera;
        Texture2D tex;
        Camera m_camera;
        Node m_node;

        public RenderCamera(Node node, GLTF.GLTFCamera data) {
            m_node = node;

            m_camera = node.gameObject.AddComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = Color.gray;
            camera.targetTexture = new RenderTexture(data.width, data.height, 24, RenderTextureFormat.Default);
            camera.targetTexture.name = "RenderTexture";
            switch (data.type) {
                case GLTF.CameraType.orthographic:
                    camera.orthographic = true;
                    camera.nearClipPlane = data.orthographic.znear;
                    camera.farClipPlane = data.orthographic.zfar;
                    camera.orthographicSize = data.orthographic.ymag;
                    break;
                case GLTF.CameraType.perspective:
                    camera.orthographic = false;
                    camera.nearClipPlane = data.perspective.znear;
                    if (data.perspective.zfar.HasValue)
                        camera.farClipPlane = data.perspective.zfar.Value;
                    if (data.perspective.aspectRatio.HasValue)
                        camera.aspect = data.perspective.aspectRatio.Value;
                    camera.fieldOfView = Mathf.Rad2Deg * data.perspective.yfov;
                    break;
            }
            UniversalAdditionalCameraData cameraData = camera.gameObject.AddComponent<UniversalAdditionalCameraData>();
            cameraData.renderPostProcessing = true;
            camera.enabled = false;
            tex = new Texture2D(camera.targetTexture.width, camera.targetTexture.height);
            if (Application.isPlaying)
                Simulator.Register(this);
        }

        public void Render(UnityAction<Color32[]> callback) {
            RenderCoroutine(callback).RunCoroutine();
        }

        public int getObservationSizes() {
            return camera.targetTexture.width * camera.targetTexture.height * 3;
        }

        public int[] getObservationShape() {
            int[] shape = { camera.targetTexture.height, camera.targetTexture.width, 3 };
            return shape;
        }

        public IEnumerator RenderCoroutine(UnityAction<Color32[]> callback) {
            camera.enabled = true; // Enable camera so that it renders in Unity's internal render loop
            yield return new WaitForEndOfFrame(); // Wait for Unity to render
            CopyRenderResultToColorBuffer(out Color32[] buffer);
            camera.enabled = false; // Disable camera for performance
            if (callback != null)
                callback(buffer);
        }

        private void CopyRenderResultToColorBuffer(out Color32[] buffer) {
            buffer = new Color32[0];
            RenderTexture activeRenderTexture = RenderTexture.active;
            RenderTexture.active = camera.targetTexture;
            tex.ReadPixels(new Rect(0, 0, tex.width, tex.height), 0, 0);
            tex.Apply();
            buffer = tex.GetPixels32();
        }
    }
}