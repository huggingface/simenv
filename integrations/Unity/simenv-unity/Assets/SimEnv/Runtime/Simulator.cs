using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Threading.Tasks;
using SimEnv.GLTF;
using UnityEngine;
using UnityEngine.Events;

namespace SimEnv {
    /// <summary>
    /// Initializes the SimEnv backend. Required for all scenes.
    /// </summary>
    public class Simulator : MonoBehaviour {
        static Simulator _instance;
        public static Simulator instance {
            get {
                if (_instance == null) {
                    _instance = GameObject.FindObjectOfType<Simulator>();
                    if (_instance == null)
                        _instance = new GameObject("Simulator").AddComponent<Simulator>();
                }
                return _instance;
            }
        }

        public static event UnityAction BeforeStep;
        public static event UnityAction AfterStep;
        public static event UnityAction AfterReset;
        public static event UnityAction BeforeIntermediateFrame;
        public static event UnityAction AfterIntermediateFrame;

        public static Dictionary<string, Type> extensions;
        public static List<IPlugin> plugins;
        public static GameObject root { get; private set; }
        public static Dictionary<string, Node> nodes { get; private set; }
        public static List<RenderCamera> cameras { get; private set; }
        public static EventData currentEvent { get; private set; }

        private void Awake() {
            Physics.autoSimulation = false;
            LoadCustomAssemblies();
            LoadPlugins();
            // TODO: Option to parse simulation args directly from API
            GetCommandLineArgs(out int port);
            Client.Initialize("localhost", port);
        }

        private void OnDestroy() {
            Unload();
            UnloadPlugins();
        }

        static void GetCommandLineArgs(out int port) {
            port = 55000;
            string[] args = System.Environment.GetCommandLineArgs();
            for (int i = 0; i < args.Length - 1; i++) {
                if (args[i] == "port")
                    int.TryParse(args[i + 1], out port);
            }
        }

        public static async Task Initialize(string b64bytes, Dictionary<string, object> kwargs) {
            if (root != null)
                throw new System.Exception("Scene is already initialized. Close before opening a new scene.");

            // Load scene from bytes
            byte[] bytes = Convert.FromBase64String(b64bytes);
            root = await Importer.LoadFromBytesAsync(bytes);

            // Gather reference to nodes and cameras
            nodes = new Dictionary<string, Node>();
            cameras = new List<RenderCamera>();
            foreach (Node node in root.GetComponentsInChildren<Node>(true)) {
                nodes.Add(node.gameObject.name, node);
                if (node.camera != null) {
                    cameras.Add(node.camera);
                }
            }

            // Override metadata from kwargs
            MetaData.instance.Parse(kwargs);
            MetaData.Apply();

            // Initialize plugins
            foreach (IPlugin plugin in plugins)
                plugin.OnSceneInitialized(kwargs);
        }

        public static IEnumerator StepCoroutine(Dictionary<string, object> kwargs) {
            if (root == null)
                throw new System.Exception("Scene is not initialized. Call `show()` to initialize the scene before stepping.");

            // Optionally override return_nodes and return_frames in step
            MetaData.instance.Parse(kwargs);
            // kwargs.TryParse<bool>("return_nodes", out bool readNodeData, MetaData.instance.returnNodes);
            // kwargs.TryParse<bool>("return_frames", out bool readCameraData, MetaData.instance.returnFrames);

            if (currentEvent == null)
                currentEvent = new EventData();

            // Execute pre-step functionality
            currentEvent.inputKwargs = kwargs;
            foreach (IPlugin plugin in plugins)
                plugin.OnBeforeStep(currentEvent);
            BeforeStep?.Invoke();

            // Perform the actual simulation
            Debug.Log($"Frame skip is {MetaData.instance.frameSkip}");
            Debug.Log($"Frame rate is {MetaData.instance.frameRate}");
            Debug.Log($"returnFrames is {MetaData.instance.returnFrames}");
            Debug.Log($"returnNodes is {MetaData.instance.returnNodes}");

            for (int i = 0; i < MetaData.instance.frameSkip; i++) {
                BeforeIntermediateFrame?.Invoke();
                Physics.Simulate(1f / MetaData.instance.frameRate);
                AfterIntermediateFrame?.Invoke();
            }

            // Perform early post-step functionality
            currentEvent = new EventData();
            OnEarlyStepInternal(MetaData.instance.returnFrames);
            foreach (IPlugin plugin in plugins)
                plugin.OnEarlyStep(currentEvent);

            yield return new WaitForEndOfFrame();

            // Perform post-step functionality
            OnStepInternal(MetaData.instance.returnNodes, MetaData.instance.returnFrames);
            foreach (IPlugin plugin in plugins)
                plugin.OnStep(currentEvent);

            AfterStep?.Invoke();
        }

        static void OnEarlyStepInternal(bool readCameraData) {
            if (readCameraData) {
                foreach (RenderCamera camera in cameras)
                    camera.camera.enabled = true;
            }
        }

        static void OnStepInternal(bool readNodeData, bool readCameraData) {
            if (readNodeData) {
                foreach (Node node in nodes.Values) {
                    if (MetaData.instance.nodeFilter == null || MetaData.instance.nodeFilter.Contains(node.name))
                        currentEvent.nodes.Add(node.name, node.GetData());
                }
            }
            if (readCameraData) {
                foreach (RenderCamera camera in cameras) {
                    if (camera.readable) {
                        camera.CopyRenderResultToBuffer(out uint[,,] buffer);
                        currentEvent.frames.Add(camera.node.name, buffer);
                    }
                    camera.camera.enabled = false;
                }
            }
        }

        public static void Reset() {
            foreach (Node node in nodes.Values)
                node.ResetState();
            foreach (IPlugin plugin in plugins)
                plugin.OnReset();
            AfterReset?.Invoke();
        }

        public static void Unload() {
            foreach (IPlugin plugin in Simulator.plugins)
                plugin.OnBeforeSceneUnloaded();
            if (root != null)
                GameObject.DestroyImmediate(root);
        }

        private static void LoadCustomAssemblies() {
            string modPath = Application.dataPath + "/Resources/Plugins";
            DirectoryInfo modDirectory = new DirectoryInfo(Application.dataPath + "/Resources/Plugins");
            if (!modDirectory.Exists) {
                Debug.LogWarning("Plugin directory doesn't exist at path: " + modPath);
                return;
            }
            foreach (FileInfo file in modDirectory.GetFiles()) {
                if (file.Extension == ".dll") {
                    Assembly.LoadFile(file.FullName);
                    Debug.Log("Loaded plugin assembly: " + file.Name);
                }
            }
        }

        private static void LoadPlugins() {
            plugins = AppDomain.CurrentDomain.GetAssemblies()
                .SelectMany(x => x.GetTypes())
                .Where(x => !x.IsInterface && !x.IsAbstract && typeof(IPlugin).IsAssignableFrom(x))
                .Select(x => (IPlugin)Activator.CreateInstance(x))
                .ToList();
            plugins.ForEach(plugin => plugin.OnCreated());

            extensions = new Dictionary<string, Type>();
            AppDomain.CurrentDomain.GetAssemblies()
                .SelectMany(x => x.GetTypes())
                .Where(x => !x.IsInterface && !x.IsAbstract && typeof(IGLTFExtension).IsAssignableFrom(x))
                .ToList().ForEach(type => {
                    extensions.Add(type.Name, type);
                });
        }

        private static void UnloadPlugins() {
            plugins.ForEach(plugin => plugin.OnReleased());
            plugins.Clear();
        }

        public static void Close() {
            Unload();
            Client.Close();
#if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
#else
            Application.Quit();
#endif
        }
    }
}