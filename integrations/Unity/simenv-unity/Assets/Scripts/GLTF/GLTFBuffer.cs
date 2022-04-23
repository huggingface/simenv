// adapted from https://github.com/Siccity/GLTFUtility/blob/master/Scripts/Spec/GLTFBuffer.cs
using System.Collections.Generic;
using Newtonsoft.Json;
using System.IO;
using System;
using System.Threading.Tasks;

public class GLTFBuffer
{
    [JsonProperty(Required = Required.Always)] public int byteLength;
    public string uri;
    public string name;

    [JsonIgnore] const string embeddedPrefix = "data:application/octet-stream;base64,";
    [JsonIgnore] const string embeddedPrefix2 = "data:application/gltf-buffer;base64,";

    public class ImportResult
    {
        public Stream stream;
        public long startOffset;

        public void Dispose() {
            stream.Dispose();
        }
    }

    public ImportResult Import(string filepath, byte[] bytefile, long binChunkStart) {
        ImportResult result = new ImportResult();

        if(uri == null) {
            if(string.IsNullOrEmpty(filepath))
                result.stream = new MemoryStream(bytefile);
            else
                result.stream = File.OpenRead(filepath);
            result.startOffset = binChunkStart + 8;
            result.stream.Position = result.startOffset;
        } else if(uri.StartsWith(embeddedPrefix)) {
            string b64 = uri.Substring(embeddedPrefix.Length, uri.Length - embeddedPrefix.Length);
            byte[] bytes = Convert.FromBase64String(b64);
            result.stream = new MemoryStream(bytes);
        } else if(uri.StartsWith(embeddedPrefix2)) {
            string b64 = uri.Substring(embeddedPrefix2.Length, uri.Length - embeddedPrefix2.Length);
            byte[] bytes = Convert.FromBase64String(b64);
            result.stream = new MemoryStream(bytes);
        } else if(SimEnv.RequestBuffer(uri, out byte[] bytes)) {
            result.stream = new MemoryStream(bytes);
        } else {
            string directoryRoot = Directory.GetParent(filepath).ToString() + "/";
            result.stream = File.OpenRead(directoryRoot + uri);
            result.startOffset = result.stream.Length - byteLength;
        }
        
        return result;
    }

    public class ImportTask : Importer.ImportTask<ImportResult[]>
    {
        public ImportTask(List<GLTFBuffer> buffers, string filepath, byte[] bytefile, long binChunkStart) : base() {
            task = new Task(() => {
                result = new ImportResult[buffers.Count];
                for(int i = 0; i < result.Length; i++)
                    result[i] = buffers[i].Import(filepath, bytefile, binChunkStart);
            });
        }
    }
}
