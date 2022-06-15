// adapted from https://github.com/Siccity/GLTFUtility/blob/master/Scripts/Spec/GLTFNode.cs
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Newtonsoft.Json;
using System;
using System.Linq;

namespace SimEnv.GLTF {
    public class GLTFNode {
        public string name;
        public int[] children;
        [JsonConverter(typeof(Matrix4x4Converter))] public Matrix4x4 matrix = Matrix4x4.identity;
        [JsonConverter(typeof(TranslationConverter))] public Vector3 translation = Vector3.zero;
        [JsonConverter(typeof(QuaternionConverter))] public Quaternion rotation = Quaternion.identity;
        [JsonConverter(typeof(Vector3Converter))] public Vector3 scale = Vector3.one;
        public int? mesh;
        public int? skin;
        public int? camera;
        public int? weights;
        public Extensions extensions;

        public bool ShouldSerializematrix() { return matrix != Matrix4x4.identity; }
        public bool ShouldSerializetranslation() { return translation != Vector3.zero; }
        public bool ShouldSerializerotation() { return rotation != Quaternion.identity; }
        public bool ShouldSerializescale() { return scale != Vector3.one; }

        public class Extensions {
            public KHR_light KHR_lights_punctual;
            public HFRLAgent HF_RL_agents;
            public HF_collider HF_collider;
        }

        public class HFRLAgent {
            public int agent;
        }

        public class KHR_light {
            public int light;
        }

        public class ImportResult {
            public int? parent;
            public int[] children;
            public Transform transform;
            public Node node;

            public bool IsRoot => !parent.HasValue;
        }

        public void ApplyMatrix(Transform transform) {
            if (matrix != Matrix4x4.identity)
                matrix.UnpackMatrix(ref translation, ref rotation, ref scale);
            transform.localPosition = translation;
            transform.localRotation = rotation;
            transform.localScale = scale;
        }

        public class ImportTask : Importer.ImportTask<ImportResult[]> {
            List<GLTFNode> nodes;
            GLTFMesh.ImportTask meshTask;
            GLTFSkin.ImportTask skinTask;
            List<GLTFCamera> cameras;
            GLTFExtensions extensions;

            public ImportTask(List<GLTFNode> nodes, GLTFMesh.ImportTask meshTask, GLTFSkin.ImportTask skinTask, List<GLTFCamera> cameras, GLTFExtensions extensions) : base(meshTask, skinTask) {
                this.nodes = nodes;
                this.meshTask = meshTask;
                this.skinTask = skinTask;
                this.cameras = cameras;
                this.extensions = extensions;
            }

            public override IEnumerator TaskCoroutine(Action<float> onProgress = null) {
                if (nodes == null) {
                    if (onProgress != null)
                        onProgress(1f);
                    IsCompleted = true;
                    yield break;
                }
                result = new ImportResult[nodes.Count];
                for (int i = 0; i < result.Length; i++) {
                    result[i] = new GLTFNode.ImportResult();
                    result[i].transform = new GameObject().transform;
                    result[i].transform.gameObject.name = nodes[i].name;
                    result[i].node = result[i].transform.gameObject.AddComponent<Node>();
                    result[i].node.Initialize();
                }
                for (int i = 0; i < result.Length; i++) {
                    if (nodes[i].children != null) {
                        int[] children = nodes[i].children;
                        result[i].children = children;
                        for (int k = 0; k < children.Length; k++) {
                            int childIndex = children[k];
                            result[childIndex].parent = i;
                            result[childIndex].transform.parent = result[i].transform;
                        }
                    }
                }
                for (int i = 0; i < result.Length; i++)
                    nodes[i].ApplyMatrix(result[i].transform);
                for (int i = 0; i < result.Length; i++) {
                    if (nodes[i].mesh.HasValue) {
                        GLTFMesh.ImportResult meshResult = meshTask.result[nodes[i].mesh.Value];
                        if (meshResult == null) continue;

                        Mesh mesh = meshResult.mesh;
                        Renderer renderer;
                        if (nodes[i].skin.HasValue) {
                            GLTFSkin.ImportResult skin = skinTask.result[nodes[i].skin.Value];
                            renderer = skin.SetupSkinnedMeshRenderer(result[i].transform.gameObject, mesh, result);
                        } else if (mesh.blendShapeCount > 0) {
                            SkinnedMeshRenderer skinnedMeshRenderer = result[i].transform.gameObject.AddComponent<SkinnedMeshRenderer>();
                            skinnedMeshRenderer.sharedMesh = mesh;
                            renderer = skinnedMeshRenderer;
                        } else {
                            MeshRenderer meshRenderer = result[i].transform.gameObject.AddComponent<MeshRenderer>();
                            MeshFilter meshFilter = result[i].transform.gameObject.AddComponent<MeshFilter>();
                            meshFilter.sharedMesh = mesh;
                            renderer = meshRenderer;
                        }
                        renderer.materials = meshResult.materials;
                        if (string.IsNullOrEmpty(result[i].transform.name))
                            result[i].transform.name = "node" + i;
                    } else {
                        if (string.IsNullOrEmpty(result[i].transform.name))
                            result[i].transform.name = "node" + i;
                    }

                    if (nodes[i].camera.HasValue) {
                        result[i].transform.localRotation *= Quaternion.Euler(0, 180, 0);
                        GLTFCamera cameraData = cameras[nodes[i].camera.Value];
                        new RenderCamera(result[i].node, cameraData);
                    }
                    if (nodes[i].extensions != null) {
                        if (nodes[i].extensions.KHR_lights_punctual != null) {
                            int lightValue = nodes[i].extensions.KHR_lights_punctual.light;
                            if (extensions == null || extensions.KHR_lights_punctual == null || extensions.KHR_lights_punctual.lights == null || extensions.KHR_lights_punctual.lights.Count < lightValue) {
                                Debug.LogWarning("Error importing light");
                            } else {
                                KHR_lights_punctual.GLTFLight lightData = extensions.KHR_lights_punctual.lights[lightValue];
                                Light light = result[i].transform.gameObject.AddComponent<Light>();
                                result[i].transform.localRotation *= Quaternion.Euler(0, 180, 0);
                                if (!string.IsNullOrEmpty(lightData.name))
                                    light.transform.gameObject.name = lightData.name;
                                light.color = lightData.color;
                                light.intensity = lightData.intensity;
                                light.range = lightData.range;
                                light.shadows = LightShadows.Soft;
                                switch(lightData.type) {
                                    case LightType.directional:
                                        light.type = UnityEngine.LightType.Directional;
                                        break;
                                    case LightType.point:
                                        light.type = UnityEngine.LightType.Point;
                                        break;
                                    case LightType.spot:
                                        light.type = UnityEngine.LightType.Spot;
                                        break;
                                }
                            }
                        }
                        if (nodes[i].extensions.HF_collider != null) {
                            HF_collider collider = nodes[i].extensions.HF_collider;
                            if (collider.mesh.HasValue) {
                                Debug.LogWarning("Ignoring collider mesh value");
                            }
                            if (collider.type == ColliderType.BOX) {
                                BoxCollider col = result[i].transform.gameObject.AddComponent<BoxCollider>();
                                col.size = collider.boundingBox;
                                col.center = collider.offset;
                                col.isTrigger = collider.intangible;
                            } else if (collider.type == ColliderType.SPHERE) {
                                SphereCollider col = result[i].transform.gameObject.AddComponent<SphereCollider>();
                                col.radius = Mathf.Min(collider.boundingBox[0], collider.boundingBox[1], collider.boundingBox[2]);
                                col.center = collider.offset;
                                col.isTrigger = collider.intangible;
                            } else if (collider.type == ColliderType.CAPSULE) {
                                CapsuleCollider col = result[i].transform.gameObject.AddComponent<CapsuleCollider>();
                                col.radius = Mathf.Min(collider.boundingBox[0], collider.boundingBox[2]);
                                col.height = collider.boundingBox[1];
                                col.center = collider.offset;
                                col.isTrigger = collider.intangible;
                            } else {
                                Debug.LogWarning(string.Format("Collider type {0} not implemented", collider.GetType()));
                            }
                        }
                        if (nodes[i].extensions.HF_RL_agents != null) {
                            int agent_id = nodes[i].extensions.HF_RL_agents.agent;
                            if (extensions == null || extensions.HF_RL_agents == null || extensions.HF_RL_agents.agents == null || extensions.HF_RL_agents.agents.Count < agent_id) {
                                Debug.LogWarning("Error importing agent");
                            } else {
                                HF_RL_agents.HF_RL_Agent agentData = extensions.HF_RL_agents.agents[agent_id];
                                new Agent(result[i].node, agentData);
                            }
                        }
                    }
                }
                IsCompleted = true;
            }
        }

        public class ExportResult : GLTFNode {
            [JsonIgnore] public Transform transform;
            [JsonIgnore] public MeshRenderer renderer;
            [JsonIgnore] public MeshFilter filter;
            [JsonIgnore] public SkinnedMeshRenderer skinnedMeshRenderer;
            [JsonIgnore] public GLTFMesh meshResult;
        }

        public static List<ExportResult> Export(Transform root) {
            List<ExportResult> nodes = new List<ExportResult>();
            CreateNodeListRecursive(root, nodes);
            return nodes;
        }

        static void CreateNodeListRecursive(Transform transform, List<ExportResult> nodes) {
            ExportResult node = new ExportResult();
            node.transform = transform;
            node.name = transform.name;
            node.translation = transform.localPosition;
            node.rotation = transform.localRotation;
            node.scale = transform.localScale;
            node.renderer = transform.gameObject.GetComponent<MeshRenderer>();
            node.filter = transform.gameObject.GetComponent<MeshFilter>();
            node.skinnedMeshRenderer = transform.gameObject.GetComponent<SkinnedMeshRenderer>();
            nodes.Add(node);
            if (transform.childCount > 0) {
                if (transform.childCount > 0) {
                    node.children = new int[transform.childCount];
                    for (int i = 0; i < node.children.Length; i++) {
                        Transform child = transform.GetChild(i);
                        node.children[i] = nodes.Count;
                        CreateNodeListRecursive(child, nodes);
                    }
                }
            }
        }
    }

    public static class GLTFNodeExtensions {
        public static GameObject GetRoot(this GLTFNode.ImportResult[] nodes) {
            GLTFNode.ImportResult[] roots = nodes.Where(x => x.IsRoot).ToArray();
            if (roots.Length == 1) {
                return roots[0].transform.gameObject;
            } else {
                GameObject root = new GameObject("Root");
                for (int i = 0; i < roots.Length; i++)
                    roots[i].transform.parent = root.transform;
                return root;
            }
        }
    }
}