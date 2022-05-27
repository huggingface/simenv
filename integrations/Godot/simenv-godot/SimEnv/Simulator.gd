extends Node

const HOST : String = "127.0.0.1"
const PORT : int = 55000
const RECONNECT_TIMEOUT: float = 3.0

const Client = preload("res://SimEnv/Bridge/Client.gd")
const Command = preload("res://SimEnv/Bridge/Command.gd")

var _client : Client = Client.new()
var _command : Command = Command.new()

func _ready() -> void:
	_client.connect("connected", _handle_client_connected)
	_client.connect("disconnected", _handle_client_disconnected)
	_client.connect("error", _handle_client_error)
	_client.connect("data", _handle_client_data)
	
	add_child(_client)
	add_child(_command)
	
	_client.connect_to_host(HOST, PORT)

func _connect_after_timeout(timeout: float) -> void:
	await get_tree().create_timer(timeout).timeout
	# _client.connect_to_host(HOST, PORT)

func _handle_client_connected() -> void:
	print("Client connected to server.")

func _handle_client_data(data: PackedByteArray) -> void:
	var sliced_data : PackedByteArray = data.slice(3)
	var str_data : String = ""
	
	for character in sliced_data:
		str_data += char(character)
	
	var json_object : JSON = JSON.new() 
	if json_object.parse(str_data) == OK:
		var json_data : Variant = json_object.get_data()
		_command.type = json_data["type"]

		if json_object.parse(json_data["contents"]) == OK:
			json_data = json_object.get_data()
			_command.content = json_data
			_command.execute()
		else:
			print("Error parsing content.")
	else:
		print("Error parsing data.")
	
	var message: PackedByteArray = [97, 99, 107] # "ack" callback
	_client.send(message)

func _handle_client_disconnected() -> void:
	print("Client disconnected from server.")
	_connect_after_timeout(RECONNECT_TIMEOUT)

func _handle_client_error() -> void:
	print("Client error.")
	_connect_after_timeout(RECONNECT_TIMEOUT)