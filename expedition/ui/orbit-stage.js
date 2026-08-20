// Headless render stage for local orbit clips. Driven by orbit_clip.py over CDP:
// it waits on __ready, steps the camera with stepOrbit(i, total), and screenshots
// once tilesSettled() holds. Not linked from the board UI.
const params = new URLSearchParams(location.search);
const lat = Number(params.get("lat"));
const lng = Number(params.get("lng"));
const CESIUM_BASE = "https://ajax.googleapis.com/ajax/libs/cesiumjs/1.105/Build/Cesium/";
window.__ready = false;
window.__failed = false;
window.CESIUM_BASE_URL = CESIUM_BASE;
let viewer = null;
let tileset = null;
let center = null;

window.stepOrbit = (frame, total) => {
  if (!viewer || !center) return false;
  const heading = Cesium.Math.toRadians(42 + (360 * frame) / (total || 120));
  viewer.camera.lookAt(center, new Cesium.HeadingPitchRange(heading, Cesium.Math.toRadians(-30), 300));
  return true;
};

window.tilesSettled = () => {
  // tilesLoaded means every imagery tile the current camera needs is resident,
  // so captures never show blurry half-loaded ground.
  if (!viewer) return false;
  return viewer.scene.globe.tilesLoaded === true;
};

async function boot() {
  try {
    const config = await (await fetch("/api/config")).json();
    if (!config.has_google_tiles || !config.satellite || !Number.isFinite(lat) || !Number.isFinite(lng)) {
      window.__failed = true;
      return;
    }
    viewer = new Cesium.Viewer("cesium", {
      imageryProvider: false,
      baseLayerPicker: false,
      geocoder: false,
      homeButton: false,
      sceneModePicker: false,
      navigationHelpButton: false,
      animation: false,
      timeline: false,
      fullscreenButton: false,
      infoBox: false,
      selectionIndicator: false,
      requestRenderMode: false,
      skyBox: false,
      skyAtmosphere: false,
    });
    // The photorealistic 3D tileset never refines under software GL, so this
    // stage orbits the satellite-imagery globe instead. Oblique Google
    // satellite at ~300 m reads as photoreal in the encoded clip.
    viewer.scene.globe.show = true;
    viewer.scene.globe.maximumScreenSpaceError = 3;
    // The whole orbit ring must stay resident or every frame re-downloads tiles.
    viewer.scene.globe.tileCacheSize = 1000;
    viewer.scene.fog.enabled = false;
    viewer.scene.backgroundColor = Cesium.Color.BLACK;
    viewer.imageryLayers.removeAll();
    viewer.imageryLayers.addImageryProvider(
      new Cesium.UrlTemplateImageryProvider({
        url: `${location.origin}${config.satellite}`,
        maximumLevel: 21,
        credit: "Google",
      })
    );
    center = Cesium.Cartesian3.fromDegrees(lng, lat, 8);
    window.stepOrbit(0, 120);
    window.__ready = true;
  } catch (err) {
    window.__failed = true;
  }
}

const css = document.createElement("link");
css.rel = "stylesheet";
css.href = `${CESIUM_BASE}Widgets/widgets.css`;
document.head.appendChild(css);
const script = document.createElement("script");
script.src = `${CESIUM_BASE}Cesium.js`;
script.onload = boot;
script.onerror = () => { window.__failed = true; };
document.head.appendChild(script);
