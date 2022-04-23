// adapted from https://github.com/Siccity/GLTFUtility/blob/master/Scripts/Editor/GLTFImporter.cs
using UnityEngine;
using UnityEditor.AssetImporters;

[ScriptedImporter(1, "gltf")]
public class GLTFImporterEditor : ScriptedImporter
{
    public ImportSettings importSettings;

    public override void OnImportAsset(AssetImportContext ctx) {
        AnimationClip[] animations;
        GameObject root = Importer.LoadFromFile(ctx.assetPath, importSettings, out animations);
        GLTFAssetUtility.SaveToAsset(root, animations, ctx, importSettings);
    }
}
