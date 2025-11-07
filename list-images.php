<?php
header('Content-Type: application/json');

// Security: only allow access to image directories
$allowed_categories = [
    'ANIME',
    'AESTHETICS',
    'CARS',
    'DC',
    'DEVOTIONAL',
    'MARVEL',
    'MOVIE POSTERS',
    'SPORTS',
    'SINGLE STICKERS',
    'FULLPAGE'
];

$category = $_GET['category'] ?? '';

if (!in_array($category, $allowed_categories)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid category']);
    exit;
}

$dir = __DIR__ . "/images/PINTEREST IMAGES/" . $category;

if (!is_dir($dir)) {
    echo json_encode([]);
    exit;
}

$files = scandir($dir);
$images = array_filter($files, function($file) {
    return !in_array($file, ['.', '..']) && 
           preg_match('/\.(jpg|jpeg|png|gif|webp)$/i', $file);
});

echo json_encode(array_values($images));