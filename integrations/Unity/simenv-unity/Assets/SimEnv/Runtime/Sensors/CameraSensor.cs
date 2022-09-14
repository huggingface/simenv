using UnityEngine;

namespace SimEnv {
    public class CameraSensor : ISensor {
        public string mName = "CameraSensor";
        public static string mType = "uint8";
        public Node node => m_node;
        public RenderCamera renderCamera => m_renderCamera;
        Texture2D tex;
        RenderCamera m_renderCamera;
        Node m_node;

        public CameraSensor(RenderCamera renderCamera) {
            m_node = node;
            m_renderCamera = renderCamera;
            renderCamera.camera.enabled = false;
            tex = new Texture2D(renderCamera.camera.targetTexture.width, renderCamera.camera.targetTexture.height);
        }

        public string GetName() {
            return mName;
        }

        public string GetSensorBufferType() {
            return mType;
        }

        public int GetSize() {
            return renderCamera.camera.targetTexture.width * renderCamera.camera.targetTexture.height * 3;
        }

        public int[] GetShape() {
            int[] shape = { 3, renderCamera.camera.targetTexture.height, renderCamera.camera.targetTexture.width };
            return shape;
        }

        public void AddObsToBuffer(Buffer buffer, int mapIndex, int actorIndex) {
            int startingIndex = mapIndex * actorIndex * GetSize();

            RenderTexture activeRenderTexture = RenderTexture.active;
            RenderTexture.active = renderCamera.camera.targetTexture;
            tex.ReadPixels(new Rect(0, 0, tex.width, tex.height), 0, 0);
            tex.Apply();
            Color32[] pixels = tex.GetPixels32();
            int channelShift = GetSize() / 3; // so we have RRRGGGBBB C,H,W order

            for (int i = 0; i < pixels.Length; i++) {
                buffer.uintBuffer[startingIndex + channelShift * 0 + i] = pixels[i].r;
                buffer.uintBuffer[startingIndex + channelShift * 1 + i] = pixels[i].g;
                buffer.uintBuffer[startingIndex + channelShift * 2 + i] = pixels[i].b;
            }
        }

        public void Enable() {
            renderCamera.camera.enabled = true;
        }

        public void Disable() {
            renderCamera.camera.enabled = false;
        }
    }
}