// TC2008B Modelación de Sistemas Multiagentes con gráficas computacionales
// C# client to interact with Python server via POST
// Sergio Ruiz-Loza, Ph.D. March 2021
using System.Collections;
using System.Collections.Generic;
using System.Text;
using UnityEditor;
using UnityEngine;
using UnityEngine.Networking;
using Newtonsoft.Json;



public class WebClient : MonoBehaviour
{
    public GameObject drone;
    private FPSController droneController;
    private int steps = 0;
    private bool setupDone = false;


string jsonPayload = @"
{
    ""M"": 37,
    ""N"": 55,
    ""drones"": 2,
    ""drone_positions"": [
        [3, 3]
    ],
    ""patrol_routes"": [
        [
            [4, 4],
            [16, 47]
        ]
    ],
    ""cameras"": 2,
    ""guards"": 1,
    ""obstacles"": [
        [
            [17, 8],
            [19, 22]
        ],
        [
            [17, 25],
            [19, 40]
        ],
        [
            [23, 8],
            [25, 22]
        ],
        [
            [23, 25],
            [25, 40]
        ],
        [
            [29, 8],
            [31, 22]
        ],
        [
            [29, 25],
            [31, 40]
        ],
        [
            [35, 8],
            [36, 22]
        ],
        [
            [35, 25],
            [36, 40]
        ],
        [
            [22, 53],
            [36, 54]
        ],
        [
            [0, 48],
            [13, 54]
        ]
    ]
}";

    IEnumerator SetupModel()
    {
        string url = "http://localhost:8585"; // Replace with the correct endpoint

        UnityWebRequest request = new UnityWebRequest(url, "POST");

        // Convert the JSON string to a byte array
        byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonPayload);

        // Set the request headers and content type
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");

        // Send the request and wait for a response
        yield return request.SendWebRequest();
        setupDone = true;
    }

    IEnumerator SendStep()
    {
        string url = "http://localhost:8585"; // Replace with the correct endpoint

        UnityWebRequest request = new UnityWebRequest(url, "PUT");

        Vector3 gridPosition = droneController.getGridPosition();

        // Create the JSON payload dynamically using the grid position
        string step_json = @"
        {
            ""drone_positions"": [
                [" + Mathf.RoundToInt(gridPosition.x) + @", " + Mathf.RoundToInt(gridPosition.z) + @"]
            ]
        }";

        // Convert the JSON string to a byte array
        byte[] bodyRaw = Encoding.UTF8.GetBytes(step_json);

        // Set the request headers and content type
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");

        // Send the request and wait for a response
        yield return request.SendWebRequest();

            // Check for errors
        if (request.result == UnityWebRequest.Result.ConnectionError || request.result == UnityWebRequest.Result.ProtocolError)
        {
            Debug.LogError($"Request error: {request.error}");
        }
        else
        {
            string jsonResponse = request.downloadHandler.text;

            var responseData = JsonConvert.DeserializeObject<ResponseData>(jsonResponse);
            if (responseData != null)
            {
                yield return StartCoroutine(droneController.MoveThroughPositions(responseData.positions));
            }
            steps++;
            Debug.Log("Step: " + steps);
        }
    }

    // Start is called before the first frame update
    void Start()
    {
        droneController = drone.GetComponent<FPSController>();
        StartCoroutine(SetupModel());
    }

    // Update is called once per frame
    void Update()
    {
        if (!droneController.isMoving && setupDone) {
            StartCoroutine(SendStep());
        }
    }
}

[System.Serializable]
public class ResponseData
{
    public List<DronePosition> positions;
}

[System.Serializable]
public class DronePosition
{
    public int x;
    public int z;
}