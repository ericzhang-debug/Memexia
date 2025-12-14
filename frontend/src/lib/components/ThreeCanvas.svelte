<script lang="ts">
import { onMount, onDestroy } from 'svelte';
import * as THREE from 'three';

export let nodeCount: number = 600;
export let nodeColor: string = '#00e5ff';
export let speed: number = 1.0;
export let animateOn: boolean = true;

let canvas: HTMLCanvasElement | null = null;
let scene: THREE.Scene;
let camera: THREE.PerspectiveCamera;
let renderer: THREE.WebGLRenderer;
let points: THREE.Points | null = null;
let material: THREE.PointsMaterial | null = null;
let links: THREE.LineSegments | null = null;
let linkMaterial: THREE.LineBasicMaterial | null = null;
let animationId: number | null = null;
let mounted = false;

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

function animate() {
    if (!renderer || !scene || !camera) return;
    if (!animateOn) return;

    animationId = requestAnimationFrame(animate);

    if (points) {
        points.rotation.y += 0.0008 * speed;
        points.rotation.x += 0.0003 * speed;
    }
    if (links) {
        links.rotation.y += 0.0008 * speed;
        links.rotation.x += 0.0003 * speed;
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

$: if (mounted) {
    if (animateOn) {
        if (!animationId) animate();
    } else {
        if (animationId) {
            cancelAnimationFrame(animationId);
            animationId = null;
        }
    }
}
</script>

<canvas bind:this={canvas} class="bg-canvas"></canvas>

<style>
canvas.bg-canvas {
    position: fixed;
    inset: 0;
    width: 100vw;
    height: 100vh;
    display: block;
    z-index: 0;
}
</style>
