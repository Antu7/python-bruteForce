<?php
session_start();
?>
<html>
    <head>
        <title>Test website</title>
    </head>
    <body>
        <form action="login.php" method="POST">
            <input type="text" name="login_field" placeholder="Login..."><br/>
            <input type="password" name="password_field" placeholder="Password..."><br/>
            <input type="submit" value="Login">
        </form>
        <?php
        if(isset($_SESSION['message'])) {
            print("<h1>".$_SESSION['message']."</h1>");
            unset($_SESSION['message']);
        }
        ?>
    </body>
</html>