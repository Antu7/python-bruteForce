<?php
session_start();
if (isset($_SESSION['logged'])) {
    unset($_SESSION['logged']);
    header("Location: index.php");
} else {
    header("Location: index.php");
}
?>