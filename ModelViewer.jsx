import React, { useState, useEffect, useRef, useMemo, Suspense } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { OrbitControls, Grid, Center, Html } from '@react-three/drei';
import * as THREE from 'three';
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader.js';
import { 
  RotateCw, 
  Grid as GridIcon, 
  Eye, 
  Box, 
  Maximize2, 
  Sparkles, 
  Palette, 
  RefreshCcw,
  Camera
} from 'lucide-react';

/**
 * Loads and renders a Wavefront OBJ model with auto-centering,
 * bounding normalization, and dynamic materials.
 */
function OBJModel({ url, materialMode, wireframe, onLoaded, onError }) {
  const [object, setObject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState(null);

  useEffect(() => {
    if (!url) {
      setObject(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setErrorMsg(null);

    const loader = new OBJLoader();
    loader.load(
      url,
      (obj) => {
        try {
          // Compute bounding box and normalize scale
          const box = new THREE.Box3().setFromObject(obj);
          const size = new THREE.Vector3();
          box.getSize(size);
          const maxDim = Math.max(size.x, size.y, size.z);
          const scale = maxDim > 0 ? 2.5 / maxDim : 1;

          obj.scale.set(scale, scale, scale);

          // Center the object at origin (0, 0, 0)
          const center = new THREE.Vector3();
          box.getCenter(center);
          obj.position.x = -center.x * scale;
          obj.position.y = -center.y * scale + (size.y * scale) / 2; // Sit on ground
          obj.position.z = -center.z * scale;

          // Process child meshes
          let totalVerts = 0;
          let totalFaces = 0;

          obj.traverse((child) => {
            if (child.isMesh) {
              child.castShadow = true;
              child.receiveShadow = true;

              if (child.geometry) {
                child.geometry.computeVertexNormals();
                const pos = child.geometry.attributes.position;
                if (pos) {
                  totalVerts += pos.count;
                  totalFaces += child.geometry.index ? child.geometry.index.count / 3 : pos.count / 3;
                }
              }
            }
          });

          setObject(obj);
          setLoading(false);
          if (onLoaded) {
            onLoaded({
              vertexCount: Math.round(totalVerts),
              faceCount: Math.round(totalFaces),
              dimensions: {
                width: size.x.toFixed(2),
                height: size.y.toFixed(2),
                depth: size.z.toFixed(2),
              }
            });
          }
        } catch (err) {
          console.error("Error processing OBJ geometry:", err);
          setErrorMsg("Failed to parse 3D mesh geometry.");
          setLoading(false);
          if (onError) onError(err.message);
        }
      },
      (xhr) => {
        // Progress callback
      },
      (err) => {
        console.error("Failed to fetch OBJ model:", err);
        setErrorMsg("Failed to load 3D model file from server.");
        setLoading(false);
        if (onError) onError("Failed to download OBJ file.");
      }
    );

    return () => {
      // Cleanup geometry/materials
      if (object) {
        object.traverse((child) => {
          if (child.isMesh) {
            if (child.geometry) child.geometry.dispose();
            if (child.material) {
              if (Array.isArray(child.material)) child.material.forEach((m) => m.dispose());
              else child.material.dispose();
            }
          }
        });
      }
    };
  }, [url]);

  // Apply materials when materialMode or wireframe changes
  useEffect(() => {
    if (!object) return;

    let mat;
    if (materialMode === 'normal') {
      mat = new THREE.MeshNormalMaterial({ wireframe });
    } else if (materialMode === 'metallic') {
      mat = new THREE.MeshStandardMaterial({
        color: '#94a3b8',
        metalness: 0.85,
        roughness: 0.2,
        wireframe,
        flatShading: false,
      });
    } else if (materialMode === 'stylized') {
      mat = new THREE.MeshStandardMaterial({
        color: '#6366f1',
        metalness: 0.2,
        roughness: 0.45,
        wireframe,
        flatShading: true,
      });
    } else {
      // Default: Clay / Studio
      mat = new THREE.MeshStandardMaterial({
        color: '#e2e8f0',
        metalness: 0.08,
        roughness: 0.75,
        wireframe,
        flatShading: false,
      });
    }

    object.traverse((child) => {
      if (child.isMesh) {
        child.material = mat;
      }
    });
  }, [object, materialMode, wireframe]);

  if (loading) {
    return (
      <Html center>
        <div className="viewer-loading-pill">
          <div className="spinner"></div>
          <span>Loading 3D Mesh...</span>
        </div>
      </Html>
    );
  }

  if (errorMsg) {
    return (
      <Html center>
        <div className="viewer-error-pill">
          <span>{errorMsg}</span>
        </div>
      </Html>
    );
  }

  if (!object) return null;

  return <primitive object={object} />;
}

/**
 * Placeholder shown before the user generates a model.
 */
function EmptyPlaceholder() {
  const meshRef = useRef();

  return (
    <group position={[0, 0.8, 0]}>
      <mesh ref={meshRef}>
        <octahedronGeometry args={[1.0, 0]} />
        <meshStandardMaterial 
          color="#6366f1" 
          wireframe 
          emissive="#4338ca" 
          emissiveIntensity={0.5} 
        />
      </mesh>
      <Html center position={[0, -1.3, 0]}>
        <div className="viewer-placeholder-hint">
          <Sparkles size={16} />
          <span>Enter a prompt & click "Generate 3D Model"</span>
        </div>
      </Html>
    </group>
  );
}

/**
 * Main 3D Model Viewer Component
 */
export default function ModelViewer({
  modelUrl,
  isLoading = false,
  onLoaded,
  onError,
}) {
  const [wireframe, setWireframe] = useState(false);
  const [autoRotate, setAutoRotate] = useState(false);
  const [showGrid, setShowGrid] = useState(true);
  const [materialMode, setMaterialMode] = useState('clay'); // clay, metallic, stylized, normal
  const controlsRef = useRef();

  const handleResetCamera = () => {
    if (controlsRef.current) {
      controlsRef.current.reset();
    }
  };

  const handleTakeSnapshot = () => {
    const canvas = document.querySelector('.model-viewer-container canvas');
    if (canvas) {
      try {
        const dataUrl = canvas.toDataURL('image/png');
        const link = document.createElement('a');
        link.download = 'polygen-3d-model.png';
        link.href = dataUrl;
        link.click();
      } catch (err) {
        console.error('Failed to take snapshot:', err);
      }
    }
  };

  return (
    <div className="model-viewer-container">
      {/* 3D WebGL Canvas */}
      <Canvas
        camera={{ position: [3.5, 2.5, 3.5], fov: 45 }}
        shadows
        gl={{ antialias: true, alpha: true, preserveDrawingBuffer: true }}
      >
        {/* Studio Lighting Rig */}
        <ambientLight intensity={0.7} />
        <directionalLight 
          position={[6, 10, 6]} 
          intensity={1.5} 
          castShadow 
          shadow-mapSize={[1024, 1024]}
        />
        <directionalLight position={[-6, 4, -6]} intensity={0.5} color="#93c5fd" />
        <hemisphereLight skyColor="#ffffff" groundColor="#334155" intensity={0.4} />

        {/* Ground Grid */}
        {showGrid && (
          <Grid
            position={[0, -0.01, 0]}
            args={[12, 12]}
            cellSize={0.5}
            cellThickness={1.0}
            cellColor="#3b82f6"
            sectionSize={2.0}
            sectionThickness={1.5}
            sectionColor="#6366f1"
            fadeDistance={25}
            fadeStrength={1.5}
          />
        )}

        {/* 3D Model or Empty Hint */}
        <Suspense fallback={null}>
          {modelUrl ? (
            <OBJModel
              url={modelUrl}
              materialMode={materialMode}
              wireframe={wireframe}
              onLoaded={onLoaded}
              onError={onError}
            />
          ) : (
            <EmptyPlaceholder />
          )}
        </Suspense>

        {/* Interactive Orbit Controls (Zoom, Pan, Rotate) */}
        <OrbitControls
          ref={controlsRef}
          enableRotate={true}
          enableZoom={true}
          enablePan={true}
          autoRotate={autoRotate}
          autoRotateSpeed={2.5}
          minDistance={0.8}
          maxDistance={15.0}
          dampingFactor={0.08}
          makeDefault
        />
      </Canvas>

      {/* Floating Viewport Toolbar */}
      <div className="viewer-toolbar">
        <button
          type="button"
          className={`toolbar-btn ${autoRotate ? 'active' : ''}`}
          onClick={() => setAutoRotate(!autoRotate)}
          title="Toggle Auto Rotation"
        >
          <RotateCw size={16} />
          <span>Rotate</span>
        </button>

        <button
          type="button"
          className={`toolbar-btn ${wireframe ? 'active' : ''}`}
          onClick={() => setWireframe(!wireframe)}
          title="Toggle Wireframe Mode"
        >
          <Box size={16} />
          <span>Wireframe</span>
        </button>

        <button
          type="button"
          className={`toolbar-btn ${showGrid ? 'active' : ''}`}
          onClick={() => setShowGrid(!showGrid)}
          title="Toggle Ground Grid"
        >
          <GridIcon size={16} />
          <span>Grid</span>
        </button>

        {/* Material Selector */}
        <div className="toolbar-select-group">
          <Palette size={15} />
          <select 
            value={materialMode} 
            onChange={(e) => setMaterialMode(e.target.value)}
            className="toolbar-select"
            title="Switch Shading Material"
          >
            <option value="clay">Clay Studio</option>
            <option value="metallic">Chrome Metal</option>
            <option value="stylized">Stylized Purple</option>
            <option value="normal">Normal Map</option>
          </select>
        </div>

        <button
          type="button"
          className="toolbar-btn"
          onClick={handleResetCamera}
          title="Reset Camera View"
        >
          <RefreshCcw size={16} />
          <span>Reset</span>
        </button>

        <button
          type="button"
          className="toolbar-btn"
          onClick={handleTakeSnapshot}
          title="Capture Snapshot Image (PNG)"
        >
          <Camera size={16} />
          <span>Snapshot</span>
        </button>
      </div>

      {/* Interaction Hint */}
      <div className="viewer-hint">
        <span>Left-click: Rotate • Right-click: Pan • Scroll: Zoom</span>
      </div>

      {/* Global generation overlay if generating */}
      {isLoading && (
        <div className="viewer-generating-overlay">
          <div className="generating-card">
            <div className="generating-spinner"></div>
            <h3>Generating 3D Asset...</h3>
            <p>Synthesizing geometry from prompt & exporting Wavefront OBJ</p>
          </div>
        </div>
      )}
    </div>
  );
}

