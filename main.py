<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>住所検索 道案内アプリ</title>

  <!-- Leaflet -->
  <link rel="stylesheet"
        href="https://unpkg.com/leaflet/dist/leaflet.css"/>

  <style>
    body {
      margin: 0;
      font-family: Arial, sans-serif;
      background: #f5f5f5;
    }

    header {
      background: #2196f3;
      color: white;
      padding: 15px;
      text-align: center;
      font-size: 24px;
    }

    .container {
      padding: 20px;
    }

    input {
      width: 100%;
      padding: 12px;
      margin-bottom: 10px;
      font-size: 16px;
      box-sizing: border-box;
    }

    button {
      width: 100%;
      padding: 12px;
      font-size: 18px;
      border: none;
      background: #2196f3;
      color: white;
      cursor: pointer;
      border-radius: 5px;
    }

    button:hover {
      background: #1976d2;
    }

    #result {
      margin-top: 15px;
      background: white;
      padding: 15px;
      border-radius: 8px;
    }

    #map {
      margin-top: 20px;
      height: 500px;
      border-radius: 10px;
    }
  </style>
</head>

<body>

<header>
  住所検索 道案内アプリ
</header>

<div class="container">

  <input type="text"
         id="start"
         placeholder="出発地住所">

  <input type="text"
         id="goal"
         placeholder="目的地住所">

  <button onclick="searchRoute()">
    ルート検索
  </button>

  <div id="result">
    距離・所要時間が表示されます
  </div>

  <div id="map"></div>

</div>

<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>

<script>

  // 地図初期化
  const map = L.map('map').setView([35.681236, 139.767125], 12);

  // OpenStreetMap
  L.tileLayer(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    {
      attribution: '&copy; OpenStreetMap'
    }
  ).addTo(map);

  let routeLayer;
  let startMarker;
  let goalMarker;

  // 住所 → 緯度経度変換
  async function geocode(address) {

    const url =
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`;

    const response = await fetch(url);

    const data = await response.json();

    if (data.length === 0) {
      throw new Error("住所が見つかりません");
    }

    return {
      lat: data[0].lat,
      lon: data[0].lon
    };
  }

  async function searchRoute() {

    const startAddress =
      document.getElementById("start").value;

    const goalAddress =
      document.getElementById("goal").value;

    if (!startAddress || !goalAddress) {
      alert("住所を入力してください");
      return;
    }

    try {

      // 住所を座標へ変換
      const start = await geocode(startAddress);
      const goal = await geocode(goalAddress);

      // ルートAPI
      const routeUrl =
        `https://router.project-osrm.org/route/v1/driving/` +
        `${start.lon},${start.lat};${goal.lon},${goal.lat}` +
        `?overview=full&geometries=geojson`;

      const routeResponse =
        await fetch(routeUrl);

      const routeData =
        await routeResponse.json();

      if (routeData.routes.length === 0) {
        alert("ルートが見つかりません");
        return;
      }

      const route = routeData.routes[0];

      // 距離
      const distance =
        (route.distance / 1000).toFixed(2);

      // 時間
      const duration =
        (route.duration / 60).toFixed(1);

      document.getElementById("result").innerHTML = `
        <h3>検索結果</h3>
        <p><strong>最短距離:</strong> ${distance} km</p>
        <p><strong>所要時間:</strong> ${duration} 分</p>
      `;

      // 古いルート削除
      if (routeLayer) {
        map.removeLayer(routeLayer);
      }

      // 古いマーカー削除
      if (startMarker) {
        map.removeLayer(startMarker);
      }

      if (goalMarker) {
        map.removeLayer(goalMarker);
      }

      // ルート描画
      routeLayer =
        L.geoJSON(route.geometry).addTo(map);

      // マーカー
      startMarker =
        L.marker([start.lat, start.lon])
          .addTo(map)
          .bindPopup("出発地")
          .openPopup();

      goalMarker =
        L.marker([goal.lat, goal.lon])
          .addTo(map)
          .bindPopup("目的地");

      // 地図ズーム
      map.fitBounds(routeLayer.getBounds());

    } catch (error) {

      console.error(error);

      alert("住所検索またはルート検索に失敗しました");
    }
  }

</script>

</body>
</html>