<script lang="ts">
import { onMount, onDestroy } from 'svelte';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

export let nodeCount: number = 600;
export let nodeColor: string = '#00e5ff';
export let speed: number = 1.0;
export let animateOn: boolean = true;

let canvas: HTMLCanvasElement | null = null;
let scene: THREE.Scene;
let camera: THREE.PerspectiveCamera;
let renderer: THREE.WebGLRenderer;
let controls: OrbitControls;
let raycaster: THREE.Raycaster;
let mouse: THREE.Vector2;
let points: THREE.Points | null = null;
let material: THREE.PointsMaterial | null = null;
let links: THREE.LineSegments | null = null;
let linkMaterial: THREE.LineBasicMaterial | null = null;
let animationId: number | null = null;
let mounted = false;
let selectedNode: number | null = null;
let popupPosition = { x: 0, y: 0 };
// keyboard movement
let activeKeys = new Set<string>();
let moveSpeed = 6; // movement sensitivity

function onKeyDown(e: KeyboardEvent) {
    const k = e.key.toLowerCase();
    if (k === 'arrowup' || k === 'arrowdown' || k === 'arrowleft' || k === 'arrowright') e.preventDefault();
    activeKeys.add(k);
}

function onKeyUp(e: KeyboardEvent) {
    activeKeys.delete(e.key.toLowerCase());
}

function createRenderer() {
    if (!canvas) return;
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setPixelRatio((typeof window !== 'undefined' && window.devicePixelRatio) || 1);
    renderer.setSize((typeof window !== 'undefined' ? window.innerWidth : 800), (typeof window !== 'undefined' ? window.innerHeight : 600));
    renderer.setClearColor(0x0b1020, 1);
}

function createCamera() {
    const w = (typeof window !== 'undefined' ? window.innerWidth : 800);
    const h = (typeof window !== 'undefined' ? window.innerHeight : 600);
    camera = new THREE.PerspectiveCamera(60, w / h, 0.1, 2000);
    camera.position.z = 350;
}

function createPoints() {
    if (!scene) return;

    if (points) {
        scene.remove(points);
        points.geometry.dispose();
        if (material) material.dispose();
        points = null;
    }
    if (links) {
        scene.remove(links);
        links.geometry.dispose();
        if (linkMaterial) linkMaterial.dispose();
        links = null;
    }

    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(nodeCount * 3);
    const colors = new Float32Array(nodeCount * 3);

    const color = new THREE.Color(nodeColor);

    for (let i = 0; i < nodeCount; i++) {
        const i3 = i * 3;
        positions[i3 + 0] = (Math.random() - 0.5) * 1200;
        positions[i3 + 1] = (Math.random() - 0.5) * 800;
        positions[i3 + 2] = (Math.random() - 0.5) * 800;

        colors[i3 + 0] = color.r;
        colors[i3 + 1] = color.g;
        colors[i3 + 2] = color.b;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    material = new THREE.PointsMaterial({
        vertexColors: true,
        size: 3,
        sizeAttenuation: true,
        transparent: true,
        opacity: 0.95,
        depthWrite: false,
        blending: THREE.AdditiveBlending
    });

    points = new THREE.Points(geometry, material);
    scene.add(points);

    // create random links between nodes
    const linkCount = Math.max(0, Math.floor(nodeCount * 1.5));
    const linkPositions = new Float32Array(linkCount * 2 * 3);

    for (let i = 0; i < linkCount; i++) {
        const a = Math.floor(Math.random() * nodeCount);
        let b = Math.floor(Math.random() * nodeCount);
        while (b === a) b = Math.floor(Math.random() * nodeCount);

        const ai3 = a * 3;
        const bi3 = b * 3;
        const li6 = i * 6;

        linkPositions[li6 + 0] = positions[ai3 + 0];
        linkPositions[li6 + 1] = positions[ai3 + 1];
        linkPositions[li6 + 2] = positions[ai3 + 2];

        linkPositions[li6 + 3] = positions[bi3 + 0];
        linkPositions[li6 + 4] = positions[bi3 + 1];
        linkPositions[li6 + 5] = positions[bi3 + 2];
    }

    const linkGeometry = new THREE.BufferGeometry();
    linkGeometry.setAttribute('position', new THREE.BufferAttribute(linkPositions, 3));
    linkMaterial = new THREE.LineBasicMaterial({ color: new THREE.Color(nodeColor), transparent: true, opacity: 0.18 });
    links = new THREE.LineSegments(linkGeometry, linkMaterial);
    scene.add(links);
}

function onMouseClick(event: MouseEvent) {
    if (!points || !renderer) return;

    const rect = renderer.domElement.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);

    const intersects = raycaster.intersectObject(points);

    if (intersects.length > 0) {
        const index = intersects[0].index;
        if (index !== undefined) {
            selectedNode = index;
            popupPosition = { x: event.clientX, y: event.clientY };
        }
    } else {
        selectedNode = null;
    }
}

function animate() {
    if (!renderer || !scene || !camera) return;

    animationId = requestAnimationFrame(animate);

    if (controls) controls.update();

    // Keyboard-driven camera movement
    if (activeKeys.size > 0) {
        const move = new THREE.Vector3();
        if (activeKeys.has('arrowup') || activeKeys.has('w')) move.z -= 1;
        if (activeKeys.has('arrowdown') || activeKeys.has('s')) move.z += 1;
        if (activeKeys.has('arrowleft') || activeKeys.has('a')) move.x -= 1;
        if (activeKeys.has('arrowright') || activeKeys.has('d')) move.x += 1;
        if (activeKeys.has('q')) move.y -= 1;
        if (activeKeys.has('e')) move.y += 1;

        if (move.lengthSq() > 0) {
            move.normalize();
            move.applyQuaternion(camera.quaternion);
            const factor = 0.6 * (moveSpeed / 6);
            camera.position.addScaledVector(move, factor);
            controls.target.addScaledVector(move, factor);
            controls.update();
        }
    }

    renderer.render(scene, camera);
}

function onResize() {
    if (!renderer || !camera) return;
    const w = (typeof window !== 'undefined' ? window.innerWidth : 800);
    const h = (typeof window !== 'undefined' ? window.innerHeight : 600);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
}

function init() {
    scene = new THREE.Scene();
    createCamera();
    createRenderer();

    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.enableZoom = true;

    raycaster = new THREE.Raycaster();
    raycaster.params.Points.threshold = 10;
    mouse = new THREE.Vector2();

    renderer.domElement.addEventListener('click', onMouseClick);
    if (typeof window !== 'undefined') {
        window.addEventListener('keydown', onKeyDown);
        window.addEventListener('keyup', onKeyUp);
    }

    createPoints();
    animate();
}

onMount(() => {
    mounted = true;
    // client-only initialization
    init();
    if (typeof window !== 'undefined') window.addEventListener('resize', onResize);
});

onDestroy(() => {
    if (typeof window !== 'undefined') window.removeEventListener('resize', onResize);
    if (renderer && renderer.domElement) {
        renderer.domElement.removeEventListener('click', onMouseClick);
    }
    if (typeof window !== 'undefined') {
        window.removeEventListener('keydown', onKeyDown);
        window.removeEventListener('keyup', onKeyUp);
    }
    if (controls) controls.dispose();
    if (animationId) cancelAnimationFrame(animationId);
    if (renderer) renderer.dispose();
    if (points) {
        points.geometry.dispose();
        if (material) material.dispose();
    }
    if (links) {
        links.geometry.dispose();
        if (linkMaterial) linkMaterial.dispose();
    }
});

$: if (mounted && material) {
    material.color = new THREE.Color(nodeColor);
    if (linkMaterial) linkMaterial.color = new THREE.Color(nodeColor);
}

$: if (mounted && scene) {
    // Recreate points when nodeCount changes
    createPoints();
}

$: if (mounted && !animationId) {
    animate();
}
</script>

<canvas bind:this={canvas} class="bg-canvas"></canvas>

{#if selectedNode !== null}
    <div class="popup" style="left: {popupPosition.x}px; top: {popupPosition.y}px;">
        <div class="popup-content">
            <h3>Node Details</h3>
            <p>ID: {selectedNode}</p>
            {#if points}
            <p>Position: 
                {points.geometry.attributes.position.getX(selectedNode).toFixed(0)}, 
                {points.geometry.attributes.position.getY(selectedNode).toFixed(0)}, 
                {points.geometry.attributes.position.getZ(selectedNode).toFixed(0)}
            </p>
            {/if}
            <button on:click|stopPropagation={() => selectedNode = null}>Close</button>
        </div>
    </div>
{/if}

<style>
canvas.bg-canvas {
    position: fixed;
    inset: 0;
    width: 100vw;
    height: 100vh;
    display: block;
    z-index: 0;
}

.popup {
    position: fixed;
    z-index: 100;
    pointer-events: none;
}

.popup-content {
    background: rgba(11, 16, 32, 0.95);
    border: 1px solid #00e5ff;
    color: #fff;
    padding: 1rem;
    border-radius: 8px;
    pointer-events: auto;
    min-width: 200px;
    box-shadow: 0 0 15px rgba(0, 229, 255, 0.3);
    transform: translate(10px, 10px);
}

.popup h3 {
    margin: 0 0 0.5rem 0;
    color: #00e5ff;
    font-size: 1.1rem;
}

.popup p {
    margin: 0.25rem 0;
    font-size: 0.9rem;
    color: #ccc;
}

.popup button {
    margin-top: 0.5rem;
    background: transparent;
    border: 1px solid #00e5ff;
    color: #00e5ff;
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8rem;
    transition: all 0.2s;
}

.popup button:hover {
    background: #00e5ff;
    color: #0b1020;
}
</style>
