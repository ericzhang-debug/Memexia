<script lang="ts">
	/**
	 * 3D Knowledge Graph Visualization Component
	 *
	 * Uses Three.js to render an interactive 3D graph of nodes and edges.
	 * Supports:
	 * - Node selection and popup details
	 * - Orbit controls for camera
	 * - WASD keyboard navigation
	 * - Force-directed layout for node positioning
	 */
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';
	import * as THREE from 'three';
	import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
	import type { Node, Edge } from '$lib/api';

	interface Props {
		nodes: Node[];
		edges: Edge[];
		seedNodeId?: string | null;
	}

	let { nodes, edges, seedNodeId = null }: Props = $props();

	const dispatch = createEventDispatcher<{
		nodeClick: { node: Node; position: { x: number; y: number } };
	}>();

	let container: HTMLDivElement;
	let scene: THREE.Scene;
	let camera: THREE.PerspectiveCamera;
	let renderer: THREE.WebGLRenderer;
	let controls: OrbitControls;
	let raycaster: THREE.Raycaster;
	let mouse: THREE.Vector2;
	let animationId: number | null = null;

	let pointsObject: THREE.Points | null = null;
	let linesObject: THREE.LineSegments | null = null;
	let nodePositions: Map<string, THREE.Vector3> = new Map();
	let nodeIndices: Map<string, number> = new Map();

	// Keyboard movement
	let activeKeys = new Set<string>();
	const moveSpeed = 5;

	function onKeyDown(e: KeyboardEvent) {
		const k = e.key.toLowerCase();
		if (['arrowup', 'arrowdown', 'arrowleft', 'arrowright', 'w', 'a', 's', 'd', 'q', 'e'].includes(k)) {
			e.preventDefault();
		}
		activeKeys.add(k);
	}

	function onKeyUp(e: KeyboardEvent) {
		activeKeys.delete(e.key.toLowerCase());
	}

	function initScene() {
		// Scene
		scene = new THREE.Scene();
		scene.background = new THREE.Color(0x0b1020);

		// Camera
		camera = new THREE.PerspectiveCamera(
			60,
			container.clientWidth / container.clientHeight,
			0.1,
			2000
		);
		camera.position.z = 200;

		// Renderer
		renderer = new THREE.WebGLRenderer({ antialias: true });
		renderer.setPixelRatio(window.devicePixelRatio);
		renderer.setSize(container.clientWidth, container.clientHeight);
		container.appendChild(renderer.domElement);

		// Controls
		controls = new OrbitControls(camera, renderer.domElement);
		controls.enableDamping = true;
		controls.dampingFactor = 0.05;
		controls.enableZoom = true;

		// Raycaster
		raycaster = new THREE.Raycaster();
		raycaster.params.Points.threshold = 10;
		mouse = new THREE.Vector2();

		// Event listeners
		renderer.domElement.addEventListener('click', onMouseClick);
		window.addEventListener('keydown', onKeyDown);
		window.addEventListener('keyup', onKeyUp);
		window.addEventListener('resize', onResize);
	}

	function createGraph() {
		// Clear existing objects
		if (pointsObject) {
			scene.remove(pointsObject);
			pointsObject.geometry.dispose();
			(pointsObject.material as THREE.Material).dispose();
		}
		if (linesObject) {
			scene.remove(linesObject);
			linesObject.geometry.dispose();
			(linesObject.material as THREE.Material).dispose();
		}

		if (nodes.length === 0) return;

		// Calculate positions using force-directed layout simulation
		nodePositions.clear();
		nodeIndices.clear();

		// Initialize positions
		nodes.forEach((node, i) => {
			nodeIndices.set(node.id, i);
			// Place nodes in a sphere initially
			const phi = Math.acos(-1 + (2 * i) / nodes.length);
			const theta = Math.sqrt(nodes.length * Math.PI) * phi;
			const radius = 100;
			nodePositions.set(
				node.id,
				new THREE.Vector3(
					radius * Math.cos(theta) * Math.sin(phi),
					radius * Math.sin(theta) * Math.sin(phi),
					radius * Math.cos(phi)
				)
			);
		});

		// Simple force simulation (just a few iterations for initial layout)
		for (let iter = 0; iter < 50; iter++) {
			// Repulsion between all nodes
			nodes.forEach((n1) => {
				const p1 = nodePositions.get(n1.id)!;
				nodes.forEach((n2) => {
					if (n1.id === n2.id) return;
					const p2 = nodePositions.get(n2.id)!;
					const diff = p1.clone().sub(p2);
					const dist = Math.max(diff.length(), 1);
					const force = diff.normalize().multiplyScalar(500 / (dist * dist));
					p1.add(force);
				});
			});

			// Attraction along edges
			edges.forEach((edge) => {
				const p1 = nodePositions.get(edge.source_id);
				const p2 = nodePositions.get(edge.target_id);
				if (p1 && p2) {
					const diff = p2.clone().sub(p1);
					const dist = diff.length();
					const force = diff.normalize().multiplyScalar(dist * 0.01);
					p1.add(force);
					p2.sub(force);
				}
			});
		}

		// Create points geometry
		const geometry = new THREE.BufferGeometry();
		const positions = new Float32Array(nodes.length * 3);
		const colors = new Float32Array(nodes.length * 3);

		nodes.forEach((node, i) => {
			const pos = nodePositions.get(node.id)!;
			positions[i * 3] = pos.x;
			positions[i * 3 + 1] = pos.y;
			positions[i * 3 + 2] = pos.z;

			// Color based on node type
			let color: THREE.Color;
			if (node.id === seedNodeId) {
				color = new THREE.Color(0xffd700); // Gold for seed
			} else if (node.node_type === 'generated') {
				color = new THREE.Color(0x00e5ff); // Cyan for AI generated
			} else {
				color = new THREE.Color(0x8b5cf6); // Purple for manual
			}
			colors[i * 3] = color.r;
			colors[i * 3 + 1] = color.g;
			colors[i * 3 + 2] = color.b;
		});

		geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
		geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

		const material = new THREE.PointsMaterial({
			vertexColors: true,
			size: 8,
			sizeAttenuation: true,
			transparent: true,
			opacity: 0.9,
			depthWrite: false,
			blending: THREE.AdditiveBlending
		});

		pointsObject = new THREE.Points(geometry, material);
		scene.add(pointsObject);

		// Create lines for edges
		const linePositions: number[] = [];
		edges.forEach((edge) => {
			const p1 = nodePositions.get(edge.source_id);
			const p2 = nodePositions.get(edge.target_id);
			if (p1 && p2) {
				linePositions.push(p1.x, p1.y, p1.z, p2.x, p2.y, p2.z);
			}
		});

		if (linePositions.length > 0) {
			const lineGeometry = new THREE.BufferGeometry();
			lineGeometry.setAttribute(
				'position',
				new THREE.Float32BufferAttribute(linePositions, 3)
			);

			const lineMaterial = new THREE.LineBasicMaterial({
				color: 0x00e5ff,
				transparent: true,
				opacity: 0.15
			});

			linesObject = new THREE.LineSegments(lineGeometry, lineMaterial);
			scene.add(linesObject);
		}
	}

	function onMouseClick(event: MouseEvent) {
		if (!pointsObject || !renderer) return;

		const rect = renderer.domElement.getBoundingClientRect();
		mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
		mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

		raycaster.setFromCamera(mouse, camera);
		const intersects = raycaster.intersectObject(pointsObject);

		if (intersects.length > 0 && intersects[0].index !== undefined) {
			const index = intersects[0].index;
			const node = nodes[index];
			if (node) {
				dispatch('nodeClick', {
					node,
					position: { x: event.clientX, y: event.clientY }
				});
			}
		}
	}

	function onResize() {
		if (!camera || !renderer || !container) return;
		camera.aspect = container.clientWidth / container.clientHeight;
		camera.updateProjectionMatrix();
		renderer.setSize(container.clientWidth, container.clientHeight);
	}

	function animate() {
		animationId = requestAnimationFrame(animate);

		if (controls) controls.update();

		// Keyboard movement
		if (activeKeys.size > 0) {
			const move = new THREE.Vector3();
			if (activeKeys.has('arrowup') || activeKeys.has('w')) move.z -= 1;
			if (activeKeys.has('arrowdown') || activeKeys.has('s')) move.z += 1;
			if (activeKeys.has('arrowleft') || activeKeys.has('a')) move.x -= 1;
			if (activeKeys.has('arrowright') || activeKeys.has('d')) move.x += 1;
			if (activeKeys.has('q')) move.y -= 1;
			if (activeKeys.has('e')) move.y += 1;

			if (move.lengthSq() > 0) {
				move.normalize().applyQuaternion(camera.quaternion);
				camera.position.addScaledVector(move, moveSpeed);
				controls.target.addScaledVector(move, moveSpeed);
			}
		}

		renderer.render(scene, camera);
	}

	onMount(() => {
		initScene();
		createGraph();
		animate();
	});

	onDestroy(() => {
		if (animationId) cancelAnimationFrame(animationId);
		if (renderer) {
			renderer.domElement.removeEventListener('click', onMouseClick);
			renderer.dispose();
		}
		window.removeEventListener('keydown', onKeyDown);
		window.removeEventListener('keyup', onKeyUp);
		window.removeEventListener('resize', onResize);
		if (controls) controls.dispose();
	});

	// Recreate graph when data changes
	$effect(() => {
		if (scene) {
			nodes; // Track dependency
			edges;
			seedNodeId;
			createGraph();
		}
	});
</script>

<div bind:this={container} class="w-full h-full"></div>
