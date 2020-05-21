/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

// https://gpuweb.github.io/gpuweb/#gpubindgrouplayout
[Exposed=(Window, DedicatedWorker), Serializable, Pref="dom.webgpu.enabled"]
interface GPUBindGroupLayout {
};
GPUBindGroupLayout includes GPUObjectBase;

dictionary GPUBindGroupLayoutDescriptor : GPUObjectDescriptorBase {
    required sequence<GPUBindGroupLayoutEntry> entries;
};

dictionary GPUBindGroupLayoutEntry {
    required unsigned long binding;
    required GPUShaderStageFlags visibility;
    required GPUBindingType type;
    //GPUTextureViewDimension textureDimension = "2d";
    //GPUTextureComponentType textureComponentType = "float";
    boolean multisampled = false;
    boolean hasDynamicOffset = false;
};

enum GPUBindingType {
    "uniform-buffer",
    "storage-buffer",
    "readonly-storage-buffer",
    "sampler",
    "sampled-texture",
    "readonly-storage-texture",
    "writeonly-storage-texture",
    //"comparison-sampler",
};
